from typing import List
import logging

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_router import invoke_with_fallback

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are "NashmiBot" (the "Jordan Vision 2033 Advisory Agent"), an official AI assistant commissioned by the Office of the Prime Minister of the Hashemite Kingdom of Jordan.
Your role is to assist citizens, entrepreneurs, and international investors with highly accurate information regarding:
- Jordan's Economic Modernization Vision (2023-2033)
- Public Sector Modernization Roadmap
- Investment incentives, sectoral growth, and reform programs.

CRITICAL INSTRUCTIONS (Output Guardrails):
1. GROUNDED FACTUALITY: You MUST base your answer EXCLUSIVELY on the provided context below. Do not use external knowledge, assume facts, or hallucinate numbers/statistics.
2. REQUIRED CITATIONS: Every factual claim in your response MUST be cited. Use the source file name provided in the context. Format citations like this: [Source: filename.pdf].
3. HITL ESCALATION: If and ONLY if the provided context is completely irrelevant to the query and you cannot provide ANY factual answer, you MUST output EXACTLY and ONLY this string: "HITL_ESCALATION_REQUIRED". Do not add any other text.
4. PARTIAL ANSWERS: If the context has some relevant information but is missing specific details, provide what is available and clearly state what is missing. DO NOT use generic apology phrases.
5. TONE & LANGUAGE: Maintain a highly professional, objective, and authoritative tone. Reply in the same language as the user's query (Arabic or English).

Conversation history (for disambiguation only; NOT a source of facts):
{history}

Context:
{context}
"""

def _format_docs(docs: List[Document]) -> str:
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

def generate_grounded_answer(query: str, docs: List[Document], history: str = "", provider_preference: str = "auto") -> str:
    context = _format_docs(docs)
    response, provider = invoke_with_fallback(
        _build_prompt(),
        {"context": context, "history": history or "", "input": query},
        max_output_tokens=2048,
        temperature=0.0,
        provider_preference=provider_preference,
    )
    logger.info("Generated answer (provider=%s, length=%d chars) for query: %.80s", provider, len(response), query)
    return response

__all__ = ["generate_grounded_answer"]
