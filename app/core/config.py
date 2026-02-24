from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # ----------------------------------
    # App General Info
    # ----------------------------------
    PROJECT_NAME: str = "Jordan Vision 2033 Advisory Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(
        default="development", 
        description="Current environment: development, testing, staging, or production"
    )

    # ----------------------------------
    # Relational Database (For HITL, Logs, Users)
    # ----------------------------------
    DATABASE_URL: str = Field(default="sqlite:///./jordan_vision_agent.db")

    # ----------------------------------
    # GCP & Vertex AI Settings (Primary Infrastructure)
    # ----------------------------------
    GCP_PROJECT_ID: str = Field(default="your-project-id", description="Google Cloud Project ID")
    GCP_LOCATION: str = Field(default="us-central1", description="GCP region for Vertex AI")
    VERTEX_INDEX_ID: str = Field(default="", description="Vertex AI Vector Search Index ID")
    VERTEX_ENDPOINT_ID: str = Field(default="", description="Vertex AI Vector Search Endpoint ID")
    GCS_BUCKET_NAME: str = Field(default="", description="GCS bucket for Vertex AI staging")

    # ----------------------------------
    # Guardrails & Operational Configs
    # ----------------------------------
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.60, 
        description="Minimum hybrid similarity score to answer. If below, escalate to HITL."
    )
    MAX_RETRIEVED_DOCS: int = 5

    # ----------------------------------
    # Optional fallback keys (not used with Vertex AI primary flow)
    # ----------------------------------
    GROQ_API_KEY: Optional[str] = Field(default=None, description="API Key for Groq Cloud (fallback)")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="API Key for OpenAI (fallback)")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()