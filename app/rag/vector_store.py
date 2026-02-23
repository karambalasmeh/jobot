import math
from typing import List
from langchain_core.documents import Document
from langchain_google_vertexai import VectorSearchVectorStore
from app.rag.embeddings import get_embeddings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Vertex AI text-embedding-004: 20K token-per-request limit
# Each 1000-char chunk ≈ 250 tokens → 50 chunks ≈ 12,500 tokens (safe)
EMBED_BATCH_SIZE = 50


def get_vector_store() -> VectorSearchVectorStore:
    """
    Returns a VectorSearchVectorStore configured for streaming mode.
    Used for both ingestion (add_documents) and retrieval (similarity_search).
    """
    project_id = settings.GCP_PROJECT_ID
    region = settings.GCP_LOCATION
    index_id = settings.VERTEX_INDEX_ID
    endpoint_id = settings.VERTEX_ENDPOINT_ID
    bucket_name = settings.GCS_BUCKET_NAME

    if not all([index_id, endpoint_id, bucket_name]):
        raise ValueError(
            "Missing Vertex AI Vector Search configuration. Check your .env file."
        )

    embeddings = get_embeddings()

    vector_store = VectorSearchVectorStore.from_components(
        project_id=project_id,
        region=region,
        gcs_bucket_name=bucket_name,
        index_id=index_id,
        endpoint_id=endpoint_id,
        embedding=embeddings,
        stream_update=True,
    )
    return vector_store


def _ensure_metadata(documents: List[Document]) -> List[Document]:
    """Guarantee every chunk has source_file and page metadata for citations."""
    for doc in documents:
        if "source_file" not in doc.metadata:
            doc.metadata["source_file"] = doc.metadata.get("source", "Unknown Source")
        if "page" not in doc.metadata:
            doc.metadata["page"] = doc.metadata.get("page_number", None)
    return documents


def build_vector_store(documents: List[Document]) -> VectorSearchVectorStore:
    """
    Upload documents to Vertex AI Vector Search via streaming.
    Uses langchain's add_documents() which:
      1. Stores document text + metadata in GCS (needed for retrieval)
      2. Embeds the text
      3. Upserts vectors via streaming API (compatible with STREAM_UPDATE index)
    
    Documents are batched to stay within the embedding token limit.
    """
    documents = _ensure_metadata(documents)
    total = len(documents)
    num_batches = math.ceil(total / EMBED_BATCH_SIZE)

    logger.info(
        f"Starting ingestion of {total} documents in {num_batches} batches "
        f"(batch size: {EMBED_BATCH_SIZE})..."
    )

    vector_store = get_vector_store()

    for i in range(num_batches):
        start = i * EMBED_BATCH_SIZE
        end = min(start + EMBED_BATCH_SIZE, total)
        batch = documents[start:end]

        logger.info(f"  Batch {i + 1}/{num_batches}: uploading docs {start + 1}–{end}...")
        vector_store.add_documents(batch)

    logger.info(
        f"Ingestion complete! {total} documents uploaded to Vertex AI. "
        "They should be queryable within a few minutes."
    )
    return vector_store