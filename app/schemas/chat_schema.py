from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str = Field(..., description="User query")
    conversation_id: Optional[int] = Field(default=None, description="Conversation ID to continue")


class SourceMetadata(BaseModel):
    document_title: str
    page_number: Optional[int] = None
    url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant answer")
    citations: List[SourceMetadata] = Field(default=[], description="Grounding citations")
    is_escalated: bool = Field(default=False, description="Escalated to human advisors (HITL)")
    ticket_id: Optional[int] = Field(default=None, description="Ticket ID (when escalated)")
    confidence_score: Optional[float] = Field(default=None, description="Top normalized score (0-1)")
    confidence_threshold: Optional[float] = Field(default=None, description="Configured threshold for escalation (0-1)")
    retrieved_scores: Optional[List[float]] = Field(default=None, description="Scores for retrieved docs")
    guardrail_status: Optional[str] = Field(default=None, description="passed | input_blocked | low_confidence | output_* | cached_*")
    conversation_id: Optional[int] = Field(default=None, description="Conversation ID used for history")
