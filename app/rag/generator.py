from typing import List
from langchain_core.documents import Document
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the "Jordan Vision 2033 Advisory Agent", an official AI assistant commissioned by the Office of the Prime Minister of the Hashemite Kingdom of Jordan.
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

def _get_llm():
    try:
        return ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
            temperature=0.0,
            max_output_tokens=2048,
            request_timeout=30.0,
        )
    except Exception as e:
        logger.warning(f"Vertex AI LLM initialization failed: {e}. Trying Groq fallback...")
        
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=0.0,
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"Groq fallback also failed: {e}")
    
    raise RuntimeError("No valid LLM provider (Vertex AI or Groq) found or accessible.")

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

def generate_grounded_answer(query: str, docs: List[Document], history: str = "") -> str:
    context = _format_docs(docs)
    chain = _build_prompt() | _get_llm() | StrOutputParser()
    response = chain.invoke({"context": context, "history": history or "", "input": query})
    logger.info("Generated answer (length=%d chars) for query: %.80s", len(response), query)
    return response

def get_rag_chain(retriever):
    chain = (
        {
            "context": retriever | RunnableLambda(_format_docs),
            "history": RunnableLambda(lambda _: ""),
            "input": RunnablePassthrough(),
        }
        | _build_prompt()
        | _get_llm()
        | StrOutputParser()
    )
    return chain
