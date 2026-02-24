from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.hitl_schema import TicketResponse, ResolveTicketRequest
from app.api.dependencies import get_db
from app.api.security import require_admin
from app.models.user import User
from app.models.ticket import Ticket
from app.services.resolved_answer_service import normalize_question, upsert_resolved_answer

router = APIRouter()

@router.get("/tickets", response_model=List[TicketResponse])
def get_open_tickets(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """استرجاع التذاكر المفتوحة فقط"""
    tickets = db.query(Ticket).filter(Ticket.status == "open").order_by(Ticket.created_at.desc()).all()
    return tickets

@router.get("/tickets/all", response_model=List[TicketResponse])
def get_all_tickets(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """استرجاع جميع التذاكر (مفتوحة ومحلولة) للمراجعة والتاريخ"""
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return tickets

@router.post("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket(ticket_id: int, request: ResolveTicketRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """إجابة الموظف البشري على التذكرة وإغلاقها"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="التذكرة غير موجودة")
    
    ticket.status = "resolved"
    ticket.human_answer = request.human_answer
    db.commit()
    db.refresh(ticket)

    # Persist resolved answers for future reuse (cross-user caching).
    upsert_resolved_answer(
        db,
        ticket_id=ticket.id,
        question=ticket.user_query,
        answer=request.human_answer,
        citations=[],
    )

    # Resolve duplicates for the same normalized question (created before ticket de-duplication).
    norm = normalize_question(ticket.user_query)
    closed = 0
    dupes = (
        db.query(Ticket)
        .filter(Ticket.status == "open")
        .order_by(Ticket.id.desc())
        .limit(500)
        .all()
    )
    for t in dupes:
        if t.id == ticket.id:
            continue
        if normalize_question(t.user_query) == norm:
            t.status = "resolved"
            t.human_answer = request.human_answer
            closed += 1
    if closed:
        db.commit()

    return ticket
