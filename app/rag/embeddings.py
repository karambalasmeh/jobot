from langchain_google_vertexai import VertexAIEmbeddings
from app.core.config import settings
import logging
import warnings

logger = logging.getLogger(__name__)

# Suppress the deprecation warning — we're using VertexAIEmbeddings intentionally
# because the project authenticates via GCP service account (not API key)
warnings.filterwarnings("ignore", message=".*VertexAIEmbeddings.*deprecated.*")


def get_embeddings() -> VertexAIEmbeddings:
    """
    تهيئة وإرجاع نموذج Vertex AI Embeddings.
    نستخدم نموذج text-embedding-004 كونه الأحدث والأكثر كفاءة للملفات النصية.
    يعتمد على مصادقة GCP (Application Default Credentials).
    """
    project_id = settings.GCP_PROJECT_ID
    location = settings.GCP_LOCATION

    if not project_id:
        raise ValueError("GCP_PROJECT_ID is not set in the environment variables.")

    embeddings = VertexAIEmbeddings(
        project=project_id,
        location=location,
        model_name="text-embedding-004",
    )

    return embeddings