
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str = Field(..., description="سؤال المواطن أو المستثمر")

class SourceMetadata(BaseModel):
    document_title: str
    page_number: Optional[int] = None
    url: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str = Field(..., description="إجابة النظام")
    citations: List[SourceMetadata] = Field(default=[], description="المصادر الحكومية المعتمدة")
    is_escalated: bool = Field(default=False, description="هل تم تحويل السؤال لموظف بشري؟")
    ticket_id: Optional[int] = Field(default=None, description="رقم التذكرة في حال التحويل")
    confidence_score: Optional[float] = Field(default=None, description="أعلى نتيجة تشابه (0-1)")
    retrieved_scores: Optional[List[float]] = Field(default=None, description="نتائج التشابه لكل المستندات")
    guardrail_status: Optional[str] = Field(default=None, description="حالة الحراسة: passed, input_blocked, low_confidence, output_*")