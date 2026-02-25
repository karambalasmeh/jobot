import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.security import get_current_user
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.rag.retriever import retrieve_relevant_documents
from app.schemas.report_schema import ReportRequest
from app.services.report_service import (
    build_docx_report,
    build_report_filename,
    convert_docx_bytes_to_pdf,
    generate_report_markdown,
)
from app.services.translation_service import is_arabic_text, translate_to_english

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_history_text(db: Session, conversation_id: int, limit: int = 10) -> str:
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    msgs = list(reversed(msgs))
    parts: list[str] = []
    for m in msgs:
        role = "User" if m.role == "user" else "Assistant"
        parts.append(f"{role}: {m.content}")
    return "\n".join(parts)


@router.post("/generate")
def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    history_text = ""
    if request.conversation_id is not None:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == request.conversation_id, Conversation.user_id == user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history_text = _build_history_text(db, conv.id, limit=10)

    retrieval_query = topic if not history_text else f"{history_text}\nReport topic: {topic}"
    retrieved_results = retrieve_relevant_documents(retrieval_query)
    all_scores = [round(min(1.0, max(0.0, float(score))), 4) for _, score in retrieved_results]
    top_score = all_scores[0] if all_scores else None

    # Same bilingual fallback as chat: translate Arabic queries to English for retrieval if needed.
    if is_arabic_text(topic) and (not retrieved_results or top_score is None or top_score < settings.CONFIDENCE_THRESHOLD):
        try:
            translated = translate_to_english(retrieval_query, provider_preference=request.provider)
            if translated and translated != retrieval_query:
                alt = retrieve_relevant_documents(translated)
                alt_scores = [round(min(1.0, max(0.0, float(score))), 4) for _, score in alt]
                alt_top = alt_scores[0] if alt_scores else None
                if alt and alt_top is not None and (top_score is None or alt_top > top_score):
                    logger.info("Report retrieval used translated query (top_score=%s -> %s)", top_score, alt_top)
                    retrieved_results = alt
        except Exception as e:
            logger.warning("Report retrieval translation fallback failed: %s", str(e))

    docs = [doc for doc, _score in retrieved_results]
    if not docs:
        raise HTTPException(status_code=400, detail="No relevant documents found to build a grounded report.")

    markdown, charts = generate_report_markdown(topic, docs, provider_preference=request.provider)
    docx_bytes = build_docx_report(
        topic=topic,
        markdown=markdown,
        charts=charts,
        retrieved_docs=docs,
        include_charts=request.include_charts,
    )

    if request.format == "pdf":
        try:
            pdf_bytes = convert_docx_bytes_to_pdf(docx_bytes)
        except Exception as e:
            logger.exception("PDF conversion failed for report topic: %s", topic[:120])
            raise HTTPException(status_code=400, detail=str(e))
        filename = build_report_filename(topic, "pdf")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = build_report_filename(topic, "docx")
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
