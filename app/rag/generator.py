from typing import List
from langchain_core.documents import Document
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ── shared system prompt ──────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are the "Jordan Vision 2033 Advisory Agent", an official AI assistant commissioned by the Office of the Prime Minister of the Hashemite Kingdom of Jordan.
Your role is to assist citizens, entrepreneurs, and international investors with highly accurate information regarding:
- Jordan's Economic Modernization Vision (2023-2033)
- Public Sector Modernization Roadmap
- Investment incentives, sectoral growth, and reform programs.

CRITICAL INSTRUCTIONS (Output Guardrails):
1. GROUNDED FACTUALITY: You MUST base your answer EXCLUSIVELY on the provided context below. Do not use external knowledge, assume facts, or hallucinate numbers/statistics.
2. REQUIRED CITATIONS: Every factual claim in your response MUST be cited. Use the source file name provided in the context. Format citations like this: [Source: filename.pdf].
3. HITL ESCALATION (Human-in-the-Loop): Use this ONLY if the provided context is completely irrelevant to the query. If you find the general topic but are missing specific details (e.g., exact hours, specific URLs, or phone numbers), provide a summary of what IS available and explicitly state which specific details are missing. Only output "HITL_ESCALATION_REQUIRED: Insufficient context to provide a verified official answer." if no relevant information at all is found.
4. TONE & LANGUAGE: Maintain a highly professional, objective, and authoritative tone. Reply in the same language as the user's query (Arabic or English). Use bullet points for readability when applicable.

Context:
{context}
"""

def _get_llm():
    """Returns the primary LLM (Vertex AI) with a fallback to Groq if needed."""
    try:
        # Try Vertex AI first (preferred)
        return ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
            temperature=0.0,
            max_output_tokens=2048,
            request_timeout=30.0, # Added timeout
        )
    except Exception as e:
        logger.warning(f"Vertex AI LLM initialization failed: {e}. Trying Groq fallback...")
        
    # Fallback to Groq if Vertex AI is unavailable or fails
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=0.0,
                timeout=30.0, # Added timeout
            )
        except Exception as e:
            logger.error(f"Groq fallback also failed: {e}")
    
    raise RuntimeError("No valid LLM provider (Vertex AI or Groq) found or accessible.")

def _format_docs(docs: List[Document]) -> str:
    """Render retrieved docs with source metadata for the prompt context."""
    parts = []
    for doc in docs:
        source = doc.metadata.get("source_file", "Unknown Source")
        parts.append(f"Content: {doc.page_content}\nSource File: {source}")
    return "\n\n---\n\n".join(parts)

def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", "{input}"),
    ])


# ── Public API ────────────────────────────────────────────────────────────────

def generate_grounded_answer(query: str, docs: List[Document]) -> str:
    """
    Generate a grounded answer given a query and pre-fetched documents.
    Used by chat.py after the confidence-gate check.
    """
    context = _format_docs(docs)
    chain = _build_prompt() | _get_llm() | StrOutputParser()
    response = chain.invoke({"context": context, "input": query})
    logger.info("Generated answer (length=%d chars) for query: %.80s", len(response), query)
    return response


def get_rag_chain(retriever):
    """
    End-to-end LCEL RAG chain with an embedded retriever.
    Useful for streaming or direct chain invocation.
    """
    chain = (
        {
            "context": retriever | RunnableLambda(_format_docs),
            "input": RunnablePassthrough(),
        }
        | _build_prompt()
        | _get_llm()
        | StrOutputParser()
    )
    return chain

