from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, cast, String, case
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.api.dependencies import get_db
from app.models.log_record import LogRecord

router = APIRouter()


class LogRecordResponse(BaseModel):
    id: int
    user_query: str
    llm_response: str
    citations: Optional[list] = []
    is_escalated: bool
    ticket_id: Optional[int] = None
    confidence_score: Optional[float] = None
    response_time_ms: Optional[int] = None
    guardrail_status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationMetrics(BaseModel):
    total_queries: int
    answered_count: int
    escalated_count: int
    answer_rate: float
    avg_confidence: Optional[float]
    avg_response_time_ms: Optional[float]
    input_blocked_count: int
    output_guardrail_count: int
    low_confidence_count: int
    queries_with_citations: int


@router.get("/logs", response_model=List[LogRecordResponse])
def get_interaction_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve recent interaction logs for diagnostics and review."""
    logs = (
        db.query(LogRecord)
        .order_by(LogRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.get("/evaluation", response_model=EvaluationMetrics)
def get_evaluation_metrics(db: Session = Depends(get_db)):
    """Compute aggregate evaluation metrics from interaction logs."""
    total = db.query(sqlfunc.count(LogRecord.id)).scalar() or 0
    escalated = db.query(sqlfunc.count(LogRecord.id)).filter(LogRecord.is_escalated == True).scalar() or 0
    answered = total - escalated

    # Clamp stored scores to [0, 1] — old data may have raw Vertex AI scores > 1.0
    clamped_score = case(
        (LogRecord.confidence_score > 1.0, 1.0),
        else_=LogRecord.confidence_score,
    )
    avg_conf = db.query(sqlfunc.avg(clamped_score)).filter(
        LogRecord.confidence_score.isnot(None)
    ).scalar()

    avg_time = db.query(sqlfunc.avg(LogRecord.response_time_ms)).filter(
        LogRecord.response_time_ms.isnot(None)
    ).scalar()

    input_blocked = db.query(sqlfunc.count(LogRecord.id)).filter(
        LogRecord.guardrail_status == "input_blocked"
    ).scalar() or 0

    output_guardrail = db.query(sqlfunc.count(LogRecord.id)).filter(
        LogRecord.guardrail_status.like("output_%")
    ).scalar() or 0

    low_conf = db.query(sqlfunc.count(LogRecord.id)).filter(
        LogRecord.guardrail_status == "low_confidence"
    ).scalar() or 0

    with_citations = db.query(sqlfunc.count(LogRecord.id)).filter(
        LogRecord.citations.isnot(None),
        cast(LogRecord.citations, String).notin_(["[]", "null", ""]),
    ).scalar() or 0

    return EvaluationMetrics(
        total_queries=total,
        answered_count=answered,
        escalated_count=escalated,
        answer_rate=round(answered / total * 100, 1) if total > 0 else 0,
        avg_confidence=round(avg_conf, 4) if avg_conf else None,
        avg_response_time_ms=round(avg_time, 0) if avg_time else None,
        input_blocked_count=input_blocked,
        output_guardrail_count=output_guardrail,
        low_confidence_count=low_conf,
        queries_with_citations=with_citations,
    )
