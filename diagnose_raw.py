import os
import sys
sys.path.append(os.getcwd())

import asyncio
from app.rag.vector_store import get_vector_store
from app.rag.bm25_store import bm25_search
from app.core.config import settings

def test_raw_scores():
    query = "What are the exact operating hours and street addresses for Future Stations in Mafraq and Karak?"
    print(f"Testing Query: {query}")
    
    # Raw Semantic Search
    try:
        vs = get_vector_store()
        semantic_raw = vs.similarity_search_with_score(query, k=5)
        print("\n--- RAW SEMANTIC RESULTS ---")
        for i, (doc, score) in enumerate(semantic_raw):
            print(f"Doc {i+1} [Raw Score: {score:.4f}]")
            print(f"Content: {doc.page_content[:100]}...")
    except Exception as e:
        print(f"\nSemantic failed: {e}")

    # Raw BM25 Search
    try:
        bm25_raw = bm25_search(query, k=5)
        print("\n--- RAW BM25 RESULTS ---")
        for i, (doc, score) in enumerate(bm25_raw):
            print(f"Doc {i+1} [Raw Score: {score:.4f}]")
            print(f"Content: {doc.page_content[:100]}...")
    except Exception as e:
        print(f"\nBM25 failed: {e}")

if __name__ == "__main__":
    test_raw_scores()
