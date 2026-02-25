from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Literal, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings

logger = logging.getLogger(__name__)

Provider = Literal["vertex", "groq"]
ProviderPreference = Literal["auto", "vertex", "groq"]


@lru_cache(maxsize=8)
def _vertex_chat_llm(*, max_output_tokens: int, temperature: float) -> Any:
    from langchain_google_vertexai import ChatVertexAI

    return ChatVertexAI(
        model_name=settings.VERTEX_LLM_MODEL,
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        # ChatVertexAI expects `timeout` (seconds). `request_timeout` is treated as model_kwargs and may not apply.
        timeout=float(settings.LLM_REQUEST_TIMEOUT_SECONDS),
    )


@lru_cache(maxsize=8)
def _groq_chat_llm(*, max_output_tokens: int, temperature: float) -> Any:
    from langchain_groq import ChatGroq

    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set; Groq fallback is unavailable.")

    # ChatGroq supports both `model` and `model_name` as aliases across versions.
    return ChatGroq(
        model=settings.GROQ_FALLBACK_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_output_tokens,
        timeout=float(settings.LLM_REQUEST_TIMEOUT_SECONDS),
    )


def invoke_with_fallback(
    prompt: ChatPromptTemplate,
    variables: dict,
    *,
    max_output_tokens: int = 2048,
    temperature: float = 0.0,
    provider_preference: ProviderPreference = "auto",
) -> Tuple[str, Provider]:
    """Invoke an LLM with Vertex/Groq, honoring a preferred provider order.

    Returns: (text, provider_used)
    """
    order: list[Provider]
    if provider_preference == "groq":
        order = ["groq", "vertex"]
    else:
        # "auto" and "vertex" both prefer Vertex first.
        order = ["vertex", "groq"]

    last_err: Exception | None = None
    for provider in order:
        try:
            llm = (
                _vertex_chat_llm(max_output_tokens=max_output_tokens, temperature=temperature)
                if provider == "vertex"
                else _groq_chat_llm(max_output_tokens=max_output_tokens, temperature=temperature)
            )
            chain = prompt | llm | StrOutputParser()
            return chain.invoke(variables), provider
        except Exception as e:
            last_err = e
            logger.warning("%s LLM call failed; trying next provider. error=%s", provider, str(e))

    # Should not happen, but keep a clear failure mode.
    raise RuntimeError("All configured LLM providers failed.") from last_err
