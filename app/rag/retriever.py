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
    semantic_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> List[Tuple[Document, float]]:
    """
    Merge semantic and BM25 results using weighted Reciprocal Rank Fusion.
    Sorts by RRF, but returns the ORIGINAL semantic score to maintain accurate confidence metrics.
    """
    doc_scores: Dict[str, Tuple[Document, float, float]] = {}

    # Semantic Search
    for rank, (doc, score) in enumerate(semantic_results):
        doc_key = doc.page_content[:200]
        rrf_score = semantic_weight * (1.0 / (k + rank + 1))
        # Store: (Document, RRF_Score, Original_Semantic_Score)
        doc_scores[doc_key] = (doc, rrf_score, score)

    # BM25 Search
    for rank, (doc, score) in enumerate(bm25_results):
        doc_key = doc.page_content[:200]
        rrf_score = bm25_weight * (1.0 / (k + rank + 1))
        if doc_key in doc_scores:
            existing_doc, existing_rrf, orig_score = doc_scores[doc_key]
            doc_scores[doc_key] = (existing_doc, existing_rrf + rrf_score, orig_score)
        else:
            # Approximate a low semantic score if only found via keyword match
            normalized_bm25 = min(1.0, score / 80.0)
            doc_scores[doc_key] = (doc, rrf_score, normalized_bm25 * 0.5)

    # Sort by fused RRF score
    sorted_results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)

    # Return the Document and its ACTUAL semantic score
    return [(item[0], item[2]) for item in sorted_results]

def _normalize_scores(results: List[Tuple[Document, float]], is_bm25: bool = False) -> List[Tuple[Document, float]]:
    if not results:
        return []
    norm_factor = 80.0 if is_bm25 else 1.0
    return [(doc, min(1.0, max(0.0, score / norm_factor))) for doc, score in results]

def retrieve_relevant_documents(query: str) -> List[Tuple[Document, float]]:
    k = settings.MAX_RETRIEVED_DOCS

    semantic_results = []
    try:
        vector_store = get_vector_store()
        semantic_results = vector_store.similarity_search_with_score(query=query, k=k)
        logger.info(f"Semantic search returned {len(semantic_results)} results")
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")

    bm25_results = []
    try:
        bm25_results = bm25_search(query, k=k)
        logger.info(f"BM25 search returned {len(bm25_results)} results")
    except Exception as e:
        logger.warning(f"BM25 search failed (non-critical): {e}")

    if semantic_results and bm25_results:
        results = _reciprocal_rank_fusion(semantic_results, bm25_results, k=60)
        logger.info(f"Hybrid RRF returned {len(results)} fused results")
    elif semantic_results:
        results = _normalize_scores(semantic_results)
    elif bm25_results:
        results = _normalize_scores(bm25_results, is_bm25=True)
    else:
        return []

    return results[:k]