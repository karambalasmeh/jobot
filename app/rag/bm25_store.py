"""
BM25 Keyword Search Index
Lightweight keyword-based retrieval using BM25 algorithm.
Stores documents in SQLite for persistence alongside Vertex AI semantic search.
"""
import json
import sqlite3
import re
from pathlib import Path
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

# SQLite DB path (alongside the main app DB)
BM25_DB_PATH = Path(__file__).resolve().parent.parent / "bm25_index.db"


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer that works for Arabic & English."""
    text = text.lower()
    # Remove punctuation but keep Arabic characters
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    return text.split()


def _init_db():
    """Create the BM25 documents table if it doesn't exist."""
    conn = sqlite3.connect(str(BM25_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bm25_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def build_bm25_index(documents: List[Document]) -> int:
    """
    Store document chunks in SQLite for BM25 keyword search.
    Clears existing data and rebuilds from scratch.
    Returns number of documents indexed.
    """
    conn = _init_db()
    conn.execute("DELETE FROM bm25_documents")

    rows = [
        (doc.page_content, json.dumps(doc.metadata, ensure_ascii=False, default=str))
        for doc in documents
    ]
    conn.executemany(
        "INSERT INTO bm25_documents (content, metadata) VALUES (?, ?)",
        rows
    )
    conn.commit()
    conn.close()

    logger.info(f"BM25 index built with {len(documents)} documents.")
    return len(documents)


def bm25_search(query: str, k: int = 5) -> List[Tuple[Document, float]]:
    """
    Search the BM25 index and return top-k documents with scores.
    Returns list of (Document, score) tuples, sorted by relevance.
    """
    conn = _init_db()
    rows = conn.execute("SELECT content, metadata FROM bm25_documents").fetchall()
    conn.close()

    if not rows:
        logger.warning("BM25 index is empty. Run ingestion first.")
        return []

    corpus = [row[0] for row in rows]
    metadata_list = [json.loads(row[1]) for row in rows]

    # Tokenize corpus and query
    tokenized_corpus = [_tokenize(text) for text in corpus]
    tokenized_query = _tokenize(query)

    if not tokenized_query:
        return []

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)

    # Get top-k indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Only include docs with non-zero BM25 score
            doc = Document(
                page_content=corpus[idx],
                metadata=metadata_list[idx]
            )
            results.append((doc, float(scores[idx])))

    return results
