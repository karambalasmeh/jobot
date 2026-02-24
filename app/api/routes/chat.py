import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.security import get_current_user
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.user import User
from app.rag.generator import generate_grounded_answer
from app.rag.retriever import retrieve_relevant_documents
from app.schemas.chat_schema import ChatRequest, ChatResponse, SourceMetadata
from app.services.guardrails import validate_input_query
from app.services.hitl_service import create_hitl_ticket, log_interaction
from app.services.output_guardrails import check_output
from app.services.resolved_answer_service import find_resolved_answer, normalize_question, upsert_resolved_answer

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_history_text(db: Session, conversation_id: int, limit: int = 10, before_id: Optional[int] = None) -> str:
    q = db.query(Message).filter(Message.conversation_id == conversation_id)
    if before_id is not None:
        q = q.filter(Message.id < before_id)

    msgs = q.order_by(Message.id.desc()).limit(limit).all()
    msgs = list(reversed(msgs))
    parts: list[str] = []
    for m in msgs:
        role = "User" if m.role == "user" else "Assistant"
        parts.append(f"{role}: {m.content}")
    return "\n".join(parts)


def _expand_retrieval_query(query: str, history_text: str) -> str:
    # Lightweight follow-up handling without an extra LLM call.
    if not history_text:
        return query
    if len(query.strip()) >= 120:
        return query
    return f"{history_text}\nFollow-up: {query}"


@router.post("/", response_model=ChatResponse)
def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    start_time = time.time()
    guardrail_status = "passed"

    # Ensure conversation exists and belongs to the user
    conversation_id: Optional[int] = request.conversation_id
    conv: Optional[Conversation] = None
    if conversation_id is None:
        title = (query[:60] + "...") if len(query) > 60 else query
        conv = Conversation(user_id=user.id, title=title or "New conversation")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
    else:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Persist user message immediately
    user_msg = Message(conversation_id=conversation_id, role="user", content=query)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Conversation memory (for follow-ups) - used for both guardrails and retrieval.
    history_text = _build_history_text(db, conversation_id, limit=10, before_id=user_msg.id)

    # LAYER 1: Input Guardrails (context-aware for follow-ups)
    if not validate_input_query(query, context=history_text):
        guardrail_status = "input_blocked"
        answer = "Your question is out of scope for this advisory agent."

        elapsed = int((time.time() - start_time) * 1000)
        db.add(
            Message(
                conversation_id=conversation_id,
                role="agent",
                content=answer,
                citations=[],
                is_escalated=False,
                guardrail_status=guardrail_status,
                response_time_ms=elapsed,
            )
        )
        db.commit()

        log_interaction(
            db,
            user_query=query,
            llm_response=answer,
            citations=[],
            is_escalated=False,
            guardrail_status=guardrail_status,
            response_time_ms=elapsed,
        )
        return ChatResponse(
            answer=answer,
            citations=[],
            is_escalated=False,
            confidence_score=None,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            retrieved_scores=None,
            guardrail_status=guardrail_status,
            conversation_id=conversation_id,
        )

    # LAYER 1.5: Resolved-answer cache (cross-user reuse for previously answered tickets)
    cached = find_resolved_answer(db, query)
    if not cached:
        # Fallback: if the ticket itself is resolved, serve from it (self-heals into resolved_answers).
        norm = normalize_question(query)
        resolved = (
            db.query(Ticket)
            .filter(Ticket.status == "resolved", Ticket.human_answer.isnot(None))
            .order_by(Ticket.id.desc())
            .limit(200)
            .all()
        )
        for tkt in resolved:
            if normalize_question(tkt.user_query) == norm:
                cached = upsert_resolved_answer(
                    db,
                    ticket_id=tkt.id,
                    question=tkt.user_query,
                    answer=tkt.human_answer or "",
                    citations=[],
                )
                break
    if cached:
        guardrail_status = "cached_resolved_answer"
        answer = cached.answer
        citations_dict = cached.citations or []
        citations_meta: list[SourceMetadata] = []
        for c in citations_dict:
            if isinstance(c, dict) and c.get("document_title"):
                citations_meta.append(
                    SourceMetadata(
                        document_title=c.get("document_title"),
                        page_number=c.get("page_number"),
                    )
                )

        elapsed = int((time.time() - start_time) * 1000)
        log_interaction(
            db,
            user_query=query,
            llm_response=answer,
            citations=citations_dict,
            is_escalated=False,
            guardrail_status=guardrail_status,
            response_time_ms=elapsed,
            confidence_score=1.0,
        )

        db.add(
            Message(
                conversation_id=conversation_id,
                role="agent",
                content=answer,
                citations=citations_dict,
                is_escalated=False,
                confidence_score=1.0,
                retrieved_scores=None,
                guardrail_status=guardrail_status,
                response_time_ms=elapsed,
            )
        )
        db.commit()

        return ChatResponse(
            answer=answer,
            citations=list({c.document_title: c for c in citations_meta}.values()),
            is_escalated=False,
            ticket_id=None,
            confidence_score=1.0,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            retrieved_scores=None,
            guardrail_status=guardrail_status,
            conversation_id=conversation_id,
        )

    retrieval_query = _expand_retrieval_query(query, history_text)

    # LAYER 2: Hybrid Retrieval (Vertex AI Semantic + BM25)
    retrieved_results = retrieve_relevant_documents(retrieval_query)
    docs = [doc for doc, score in retrieved_results]

    all_scores = [round(min(1.0, max(0.0, float(score))), 4) for _, score in retrieved_results]
    top_score = all_scores[0] if all_scores else None

    is_escalated = False
    ticket_id = None
    citations: list[SourceMetadata] = []

    # LAYER 3: Confidence Gate
    if not retrieved_results or top_score is None or top_score < settings.CONFIDENCE_THRESHOLD:
        is_escalated = True
        guardrail_status = "low_confidence"
        answer = "This query requires specialized human review. A ticket has been created."
        ticket_id = create_hitl_ticket(db, query)
        logger.info("HITL escalation: low confidence (top_score=%s) for query: %s", top_score, query[:80])
    else:
        # LAYER 4: Generation (Vertex AI Gemini)
        answer = generate_grounded_answer(query, docs, history=history_text)

        # LAYER 5: Output Guardrails
        guard_result = check_output(answer, citations_available=len(docs) > 0)
        if guard_result.should_escalate:
            is_escalated = True
            guardrail_status = f"output_{guard_result.reason}"
            answer = "This query requires specialized human review. A ticket has been created."
            ticket_id = create_hitl_ticket(db, query)
            logger.info("HITL escalation: output guardrail (reason=%s)", guard_result.reason)
        else:
            for doc in docs:
                source = doc.metadata.get("source_file", "Unknown Document")
                clean_title = source.replace("_", " ").replace("-", " ")
                if clean_title.lower().endswith(".pdf"):
                    clean_title = clean_title[:-4]
                citations.append(
                    SourceMetadata(
                        document_title=clean_title,
                        page_number=doc.metadata.get("page", None),
                    )
                )

    unique_citations = list({c.document_title: c for c in citations}.values())

    elapsed = int((time.time() - start_time) * 1000)
    citations_dict = [{"document_title": c.document_title, "page_number": c.page_number} for c in unique_citations]

    log_interaction(
        db,
        user_query=query,
        llm_response=answer,
        citations=citations_dict,
        is_escalated=is_escalated,
        ticket_id=ticket_id,
        confidence_score=top_score,
        response_time_ms=elapsed,
        guardrail_status=guardrail_status,
    )

    # Persist assistant message
    db.add(
        Message(
            conversation_id=conversation_id,
            role="agent",
            content=answer,
            citations=citations_dict,
            is_escalated=is_escalated,
            ticket_id=ticket_id,
            confidence_score=top_score,
            retrieved_scores=all_scores,
            guardrail_status=guardrail_status,
            response_time_ms=elapsed,
        )
    )
    db.commit()

    return ChatResponse(
        answer=answer,
        citations=unique_citations,
        is_escalated=is_escalated,
        ticket_id=ticket_id,
        confidence_score=top_score,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        retrieved_scores=all_scores,
        guardrail_status=guardrail_status,
        conversation_id=conversation_id,
    )
