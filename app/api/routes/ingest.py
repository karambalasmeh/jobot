from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.rag.document_loader import load_documents
from app.rag.text_splitter import split_documents
from app.rag.vector_store import build_vector_store
from app.rag.bm25_store import build_bm25_index

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestResponse(BaseModel):
    status: str
    message: str
    total_documents: int
    total_chunks: int
    bm25_indexed: int

@router.post("/", response_model=IngestResponse)
def ingest_data():
    """
    Read PDF files from the data directory, split into chunks,
    embed and store in Vertex AI Vector Search + BM25 keyword index.
    """
    try:
        # 1. Load documents
        logger.info("Starting document loading...")
        raw_docs = load_documents()
        if not raw_docs:
            raise HTTPException(status_code=404, detail="No PDF documents found in the data directory.")
        
        # 2. Split into chunks
        logger.info(f"Loaded {len(raw_docs)} pages. Starting text splitting...")
        chunks = split_documents(raw_docs)
        
        # 3. Build Vertex AI Vector Store (semantic search)
        logger.info(f"Created {len(chunks)} chunks. Uploading to Vertex AI...")
        build_vector_store(chunks)
        
        # 4. Build BM25 keyword index (hybrid search)
        logger.info("Building BM25 keyword index...")
        bm25_count = build_bm25_index(chunks)
        
        logger.info("Data ingestion completed successfully.")
        
        return IngestResponse(
            status="success",
            message=f"Data successfully ingested: {len(raw_docs)} documents → {len(chunks)} chunks uploaded to Vertex AI + BM25 index.",
            total_documents=len(raw_docs),
            total_chunks=len(chunks),
            bm25_indexed=bm25_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))