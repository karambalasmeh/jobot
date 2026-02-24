from sqlalchemy.orm import Session
from app.models import Ticket, LogRecord
from typing import List, Optional
from app.services.resolved_answer_service import normalize_question

def create_hitl_ticket(db: Session, user_query: str) -> int:
    """Create a new HITL ticket and return its ID.

    De-duplicates identical open tickets to avoid queue spam on repeated queries.
    """
    norm = normalize_question(user_query)
    recent_open = (
        db.query(Ticket)
        .filter(Ticket.status == "open")
        .order_by(Ticket.id.desc())
        .limit(200)
        .all()
    )
    for t in recent_open:
        if normalize_question(t.user_query) == norm:
            return t.id

    new_ticket = Ticket(
        user_query=user_query,
        status="open"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket.id

def log_interaction(
    db: Session, 
    user_query: str, 
    llm_response: str, 
    citations: List[dict], 
    is_escalated: bool, 
    ticket_id: Optional[int] = None,
    confidence_score: Optional[float] = None,
    response_time_ms: Optional[int] = None,
    guardrail_status: Optional[str] = None,
):
    """Save full interaction details for auditing and evaluation."""
    new_log = LogRecord(
        user_query=user_query,
        llm_response=llm_response,
        citations=citations,
        is_escalated=is_escalated,
        ticket_id=ticket_id,
        confidence_score=confidence_score,
        response_time_ms=response_time_ms,
        guardrail_status=guardrail_status,
    )
    db.add(new_log)
    db.commit()
