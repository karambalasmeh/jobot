"""
Input Guardrails Service
Validates incoming user queries before they reach the RAG pipeline.
Provides scope control, query validation, and prompt safety filtering.
"""
from langchain_core.prompts import ChatPromptTemplate
from app.rag.generator import _get_llm
from app.core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Fast keyword pre-check (no LLM needed)
# ──────────────────────────────────────────────

MAX_QUERY_LENGTH = 1000
MIN_QUERY_LENGTH = 3

# Obviously off-topic or unsafe terms — reject immediately without LLM call
BLOCKED_TERMS = [
    # Harmful / unsafe
    "bomb", "weapon", "kill", "attack", "hack", "exploit", "virus", "malware",
    "قنبلة", "سلاح", "اغتيال", "قرصنة", "فيروس",
    # Clearly out of scope topics
    "recipe", "وصفة", "طبخ", "cooking",
    "football", "soccer", "كرة القدم",
    "movie", "فيلم", "مسلسل",
    "dating", "love", "relationship", "حب", "تعارف",
]

# Weak signals of Jordan/economy relevance — if any present, skip LLM call (fast path)
JORDAN_KEYWORDS = [
    "jordan", "الأردن", "أردن",
    "رؤية", "vision", "2033", "2023",
    "اقتصاد", "economy", "economic",
    "استثمار", "investment", "invest",
    "قطاع عام", "public sector",
    "إصلاح", "reform",
    "حكومة", "government",
    "تحديث", "moderniz",
    "سياحة", "tourism",
    "نقل", "transport",
    "طاقة", "energy",
    "رقمي", "digital",
    "ريادة", "entrepreneurship",
    "تجارة", "trade",
    "صناعة", "industry",
]


def _fast_precheck(query: str) -> str:
    """
    Returns 'BLOCKED', 'VALID' (fast pass), or 'UNCERTAIN' (needs LLM check).
    """
    # Length validation
    if len(query.strip()) < MIN_QUERY_LENGTH:
        return "BLOCKED"
    if len(query) > MAX_QUERY_LENGTH:
        return "BLOCKED"

    query_lower = query.lower()

    # Hard-block known unsafe/off-topic terms
    for term in BLOCKED_TERMS:
        if term in query_lower:
            logger.warning("Input guardrail: fast block on term '%s'", term)
            return "BLOCKED"

    # Fast-pass for clearly Jordan/economy-related queries
    for kw in JORDAN_KEYWORDS:
        if kw in query_lower:
            return "VALID"

    # Ambiguous — hand off to LLM classifier
    return "UNCERTAIN"


def validate_input_query(query: str) -> bool:
    """
    Main entry point. Returns True if query is in scope, False if it should be rejected.
    """
    precheck = _fast_precheck(query)

    if precheck == "BLOCKED":
        return False
    if precheck == "VALID":
        logger.debug("Input guardrail: fast-pass for query (Jordan keyword matched)")
        return True

    # UNCERTAIN — use LLM classifier
    try:
        llm = _get_llm()

        system_prompt = """You are a strict classifier for the 'Jordan Vision 2033 Advisory Agent'.
Classify if the user's query is related to:
- Jordan's Economic Modernization Vision (2023-2033)
- Jordan's Public Sector Modernization Roadmap
- Investment, economic reforms, sectors, or governance in Jordan

Output EXACTLY one word: VALID or INVALID. No other text."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}")
        ])

        chain = prompt | llm
        response = chain.invoke({"query": query})
        result = response.content.strip().upper()

        if "INVALID" in result:
            logger.warning("Input guardrail: LLM classified as out-of-scope: %s", query[:80])
            return False

        return True

    except Exception as e:
        logger.error("Input guardrail LLM check failed: %s — defaulting to PASS", str(e))
        # Fail open: don't break the system if the guardrail LLM is unavailable
        return True