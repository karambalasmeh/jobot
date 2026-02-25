from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=2000, description="Report subject/topic.")
    format: Literal["docx", "pdf"] = Field(default="docx", description="Output file format.")
    conversation_id: Optional[int] = Field(default=None, description="Optional conversation to use as context.")
    include_charts: bool = Field(default=True, description="Whether to include charts if available.")
    provider: Literal["auto", "vertex", "groq"] = Field(
        default="auto",
        description="LLM provider preference: auto (Vertex->Groq), vertex, or groq.",
    )
