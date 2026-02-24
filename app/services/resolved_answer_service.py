import re
from difflib import SequenceMatcher
from typing import Optional

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.models.resolved_answer import ResolvedAnswer


def normalize_question(text: str) -> str:
    text = text.strip().lower()
    # Normalize punctuation and whitespace so "same question" matches even with minor formatting differences.
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return [t for t in text.split() if t]


def upsert_resolved_answer(
    db: Session,
    *,
    ticket_id: int,
    question: str,
    answer: str,
    citations: Optional[list] = None,
) -> ResolvedAnswer:
    normalized = normalize_question(question)
    existing = db.query(ResolvedAnswer).filter(ResolvedAnswer.ticket_id == ticket_id).first()
    payload = {
        "ticket_id": ticket_id,
        "question": question,
        "normalized_question": normalized,
        "answer": answer,
        "citations": citations or [],
    }
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    ra = ResolvedAnswer(**payload)
    db.add(ra)
    db.commit()
    db.refresh(ra)
    return ra


def find_resolved_answer(db: Session, query: str) -> Optional[ResolvedAnswer]:
    normalized = normalize_question(query)
    exact = db.query(ResolvedAnswer).filter(ResolvedAnswer.normalized_question == normalized).first()
    if exact:
        return exact

    rows = db.query(ResolvedAnswer).all()
    if not rows:
        return None

    # Backwards-compatible exact check (for rows created with an older normalizer).
    for r in rows:
        if normalize_question(r.question) == normalized:
            return r

    corpus_tokens = [_tokenize(r.question) for r in rows]
    query_tokens = _tokenize(query)
    if not query_tokens:
        return None

    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query_tokens)
    best_idx = max(range(len(scores)), key=lambda i: scores[i])
    best_score = float(scores[best_idx])

    # Near-exact check using normalized text similarity.
    best_row = rows[best_idx]
    ratio = SequenceMatcher(None, normalized, normalize_question(best_row.question)).ratio()
    if ratio >= 0.92:
        return best_row

    # Conservative keyword threshold to reduce false positives. Tune with real data.
    if best_score < 5.0:
        return None

    return best_row
