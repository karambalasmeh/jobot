import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat_schema import ChatRequest, ChatResponse, SourceMetadata
from app.api.dependencies import get_db
from app.rag.retriever import retrieve_relevant_documents
from app.rag.generator import generate_grounded_answer
from app.core.config import settings
from app.services.guardrails import validate_input_query
from app.services.output_guardrails import check_output
from app.services.hitl_service import create_hitl_ticket, log_interaction
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    query = request.query
    start_time = time.time()
    guardrail_status = "passed"

    # ── LAYER 1: Input Guardrails ─────────────────────────────────────────────
    if not validate_input_query(query):
        guardrail_status = "input_blocked"
        answer = (
            "عذراً، بصفتي المساعد الذكي لرؤية التحديث الاقتصادي، لا يمكنني الإجابة "
            "إلا على الأسئلة المتعلقة بالرؤية الاقتصادية، الاستثمار، وخارطة تحديث القطاع العام في الأردن."
        )
        elapsed = int((time.time() - start_time) * 1000)
        log_interaction(
            db, user_query=query, llm_response=answer, citations=[],
            is_escalated=False, guardrail_status=guardrail_status,
            response_time_ms=elapsed,
        )
        return ChatResponse(
            answer=answer, citations=[], is_escalated=False,
            confidence_score=None, retrieved_scores=None,
            guardrail_status=guardrail_status,
        )

    # ── LAYER 2: Hybrid Retrieval (Vertex AI Semantic + BM25) ────────────────
    retrieved_results = retrieve_relevant_documents(query)
    docs = [doc for doc, score in retrieved_results]

    # Extract similarity scores and clamp to 0–1 range
    # (Vertex AI may return raw distance scores > 1.0)
    all_scores = [round(min(1.0, max(0.0, float(score))), 4) for _, score in retrieved_results]
    top_score = all_scores[0] if all_scores else None

    is_escalated = False
    ticket_id = None
    citations = []

    # ── LAYER 3: Confidence Gate (Hybrid Score Check) ────────────────────────
    if not retrieved_results or top_score is None or top_score < settings.CONFIDENCE_THRESHOLD:
        is_escalated = True
        guardrail_status = "low_confidence"
        answer = (
            "عذراً، لم أتمكن من العثور على إجابة دقيقة وموثقة لسؤالك ضمن المستندات الرسمية. "
            "تم تحويل سؤالك إلى فريق المستشارين المتخصصين وسيتم الرد عليك في أقرب وقت."
        )
        ticket_id = create_hitl_ticket(db, query)
        logger.info("HITL escalation: low confidence (top_score=%s) for query: %s", top_score, query[:80])

    else:
        # ── LAYER 4: Generation (Vertex AI Gemini) ───────────────────────────
        answer = generate_grounded_answer(query, docs)

        # ── LAYER 5: Output Guardrails ────────────────────────────────────────
        guard_result = check_output(answer, citations_available=len(docs) > 0)

        if guard_result.should_escalate:
            is_escalated = True
            guardrail_status = f"output_{guard_result.reason}"
            answer = (
                "عذراً، بعد البحث الدقيق لم أتمكن من العثور على معلومات مؤكدة لسؤالك "
                "في المستندات الرسمية. تم تحويل استفسارك إلى فريق المستشارين."
            )
            ticket_id = create_hitl_ticket(db, query)
            logger.info("HITL escalation: output guardrail (reason=%s)", guard_result.reason)
        else:
            # Build citations only for valid, grounded answers
            for doc in docs:
                source = doc.metadata.get("source_file", "Unknown Document")
                clean_title = source.replace("_", " ").replace("-", " ")
                if clean_title.lower().endswith(".pdf"):
                    clean_title = clean_title[:-4]
                citations.append(SourceMetadata(
                    document_title=clean_title,
                    page_number=doc.metadata.get("page", None)
                ))

    # ── De-duplicate citations ─────────────────────────────────────────────────
    unique_citations = list({c.document_title: c for c in citations}.values())

    # ── LAYER 6: Logging & Audit ──────────────────────────────────────────────
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

    # ── Return response ───────────────────────────────────────────────────────
    return ChatResponse(
        answer=answer,
        citations=unique_citations,
        is_escalated=is_escalated,
        ticket_id=ticket_id,
        confidence_score=top_score,
        retrieved_scores=all_scores,
        guardrail_status=guardrail_status,
    )