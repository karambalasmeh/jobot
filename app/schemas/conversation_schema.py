from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=255)


class ConversationListItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Any = None
    is_escalated: bool
    ticket_id: Optional[int] = None
    confidence_score: Optional[float] = None
    retrieved_scores: Any = None
    guardrail_status: Optional[str] = None
    response_time_ms: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(BaseModel):
    id: int
    title: str
    messages: list[MessageResponse]

