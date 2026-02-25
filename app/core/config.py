from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field
from typing import Optional
import secrets

class Settings(BaseSettings):
    # ----------------------------------
    # App General Info
    # ----------------------------------
    PROJECT_NAME: str = "NashmiBot"
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

    # ----------------------------------
    # LLM Models (Vertex primary, Groq fallback)
    # ----------------------------------
    VERTEX_LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Vertex AI chat model name (primary).",
    )
    GROQ_FALLBACK_MODEL: str = Field(
        default="llama3-70b-8192",
        validation_alias=AliasChoices("GROQ_FALLBACK_MODEL", "MAIN_LLM_MODEL"),
        description="Groq chat model name (fallback). Falls back to MAIN_LLM_MODEL for backward compatibility.",
    )
    LLM_REQUEST_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="Timeout (seconds) for LLM requests (Vertex/Groq).",
    )

    # ----------------------------------
    # Auth (JWT)
    # ----------------------------------
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(48),
        description="JWT signing secret. Set in .env for stable sessions.",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    # ----------------------------------
    # Admin bootstrap (optional)
    # ----------------------------------
    ADMIN_BOOTSTRAP_USERNAME: Optional[str] = Field(default=None, description="Create/update this admin user on startup")
    ADMIN_BOOTSTRAP_PASSWORD: Optional[str] = Field(default=None, description="Admin password used on startup bootstrap")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
