from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "hitl_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    status = Column(String, default="open", index=True)
    human_answer = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())