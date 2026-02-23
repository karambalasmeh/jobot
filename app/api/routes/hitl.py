from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.hitl_schema import TicketResponse, ResolveTicketRequest
from app.api.dependencies import get_db
from app.models.ticket import Ticket

router = APIRouter()

@router.get("/tickets", response_model=List[TicketResponse])
def get_open_tickets(db: Session = Depends(get_db)):
    """استرجاع التذاكر المفتوحة فقط"""
    tickets = db.query(Ticket).filter(Ticket.status == "open").order_by(Ticket.created_at.desc()).all()
    return tickets

@router.get("/tickets/all", response_model=List[TicketResponse])
def get_all_tickets(db: Session = Depends(get_db)):
    """استرجاع جميع التذاكر (مفتوحة ومحلولة) للمراجعة والتاريخ"""
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return tickets

@router.post("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket(ticket_id: int, request: ResolveTicketRequest, db: Session = Depends(get_db)):
    """إجابة الموظف البشري على التذكرة وإغلاقها"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="التذكرة غير موجودة")
    
    ticket.status = "resolved"
    ticket.human_answer = request.human_answer
    db.commit()
    db.refresh(ticket)
    return ticket