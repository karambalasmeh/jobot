from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.security import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation_schema import (
    ConversationDetail,
    ConversationListItem,
    CreateConversationRequest,
    MessageResponse,
)
from app.services.text_repair import repair_utf8_mojibake_cp1252


router = APIRouter()


@router.get("/", response_model=list[ConversationListItem])
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.id.desc())
        .all()
    )
    changed = False
    for c in convs:
        if not c.title:
            continue
        fixed = repair_utf8_mojibake_cp1252(c.title)
        if fixed != c.title:
            c.title = fixed
            changed = True
    if changed:
        db.commit()
    return convs


@router.post("/", response_model=ConversationListItem)
def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = Conversation(user_id=user.id, title=request.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conv.title:
        fixed = repair_utf8_mojibake_cp1252(conv.title)
        if fixed != conv.title:
            conv.title = fixed
            db.commit()

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.id.asc())
        .all()
    )

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )
