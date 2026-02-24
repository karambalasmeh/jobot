from sqlalchemy import Column, Integer, Text, DateTime, JSON, String
from sqlalchemy.sql import func

from app.core.database import Base


class ResolvedAnswer(Base):
    __tablename__ = "resolved_answers"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, unique=True, index=True, nullable=False)

    question = Column(Text, nullable=False)
    normalized_question = Column(String(512), index=True, nullable=False)

    answer = Column(Text, nullable=False)
    citations = Column(JSON, default=[])

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

