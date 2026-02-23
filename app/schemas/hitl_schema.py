from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TicketResponse(BaseModel):
    id: int
    user_query: str
    status: str
    created_at: datetime
    human_answer: Optional[str] = None
    
    # للسماح لـ Pydantic بقراءة البيانات مباشرة من كائنات SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

class ResolveTicketRequest(BaseModel):
    human_answer: str