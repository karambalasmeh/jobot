from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base

class LogRecord(Base):
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=False)
    citations = Column(JSON, default=[])
    is_escalated = Column(Boolean, default=False)
    ticket_id = Column(Integer, nullable=True)

    # Evaluation & monitoring fields
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    guardrail_status = Column(String, nullable=True)  # "passed", "input_blocked", "output_escalated"

    created_at = Column(DateTime(timezone=True), server_default=func.now())