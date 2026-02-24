from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)

    # "user" | "agent" (keep aligned with frontend roles)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)

    citations = Column(JSON, default=[])
    is_escalated = Column(Boolean, default=False)
    ticket_id = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    retrieved_scores = Column(JSON, nullable=True)
    guardrail_status = Column(String(64), nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

