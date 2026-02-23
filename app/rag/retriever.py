from typing import List, Tuple, Dict
from langchain_core.documents import Document
from app.rag.vector_store import get_vector_store
from app.rag.bm25_store import bm25_search
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _reciprocal_rank_fusion(
    semantic_results: List[Tuple[Document, float]],
    bm25_results: List[Tuple[Document, float]],
    k: int = 60,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> List[Tuple[Document, float]]:
    """
    Merge semantic and BM25 results using weighted Reciprocal Rank Fusion.
    Returns deduplicated results sorted by fused score, normalized to 0–1.
    """
    doc_scores: Dict[str, Tuple[Document, float]] = {}

    # Score from semantic search (rank-based)
    for rank, (doc, score) in enumerate(semantic_results):
        doc_key = doc.page_content[:200]  # Use text prefix as dedup key
        rrf_score = semantic_weight * (1.0 / (k + rank + 1))
        if doc_key in doc_scores:
            existing_doc, existing_score = doc_scores[doc_key]
            doc_scores[doc_key] = (existing_doc, existing_score + rrf_score)
        else:
            doc_scores[doc_key] = (doc, rrf_score)

    # Score from BM25 search (rank-based)
    for rank, (doc, score) in enumerate(bm25_results):
        doc_key = doc.page_content[:200]
        rrf_score = bm25_weight * (1.0 / (k + rank + 1))
        if doc_key in doc_scores:
            existing_doc, existing_score = doc_scores[doc_key]
            doc_scores[doc_key] = (existing_doc, existing_score + rrf_score)
        else:
            doc_scores[doc_key] = (doc, rrf_score)

    # Sort by fused score
    sorted_results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)

    # Normalize scores to 0–1 range
    if sorted_results:
        max_score = sorted_results[0][1]
        if max_score > 0:
            sorted_results = [(doc, score / max_score) for doc, score in sorted_results]

    return sorted_results


def retrieve_relevant_documents(query: str) -> List[Tuple[Document, float]]:
    """
    Hybrid retrieval: combines Vertex AI semantic search with BM25 keyword search.
    Uses Reciprocal Rank Fusion to merge results.
    Falls back to semantic-only if BM25 is unavailable.
    """
    k = settings.MAX_RETRIEVED_DOCS

    # ── Semantic Search (Vertex AI) ──
    semantic_results = []
    try:
        vector_store = get_vector_store()
        semantic_results = vector_store.similarity_search_with_score(
            query=query,
            k=k,
        )
        logger.info(f"Semantic search returned {len(semantic_results)} results")
        for i, (doc, score) in enumerate(semantic_results):
            source = doc.metadata.get("source_file", "Unknown")
            logger.info(f"  Semantic [{i+1}] score={score:.4f} source={source} text={doc.page_content[:80]}...")
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")

    # ── BM25 Keyword Search ──
    bm25_results = []
    try:
        bm25_results = bm25_search(query, k=k)
        logger.info(f"BM25 search returned {len(bm25_results)} results")
        for i, (doc, score) in enumerate(bm25_results):
            source = doc.metadata.get("source_file", "Unknown")
            logger.info(f"  BM25 [{i+1}] score={score:.4f} source={source} text={doc.page_content[:80]}...")
    except Exception as e:
        logger.warning(f"BM25 search failed (non-critical): {e}")

    # ── Hybrid Fusion ──
    if semantic_results and bm25_results:
        fused = _reciprocal_rank_fusion(semantic_results, bm25_results)
        logger.info(f"Hybrid RRF returned {len(fused)} fused results")
        return fused[:k]
    elif semantic_results:
        logger.info("Using semantic-only results (BM25 unavailable)")
        return semantic_results
    elif bm25_results:
        logger.info("Using BM25-only results (semantic unavailable)")
        return bm25_results
    else:
        logger.error("Both semantic and BM25 search returned no results!")
        return []