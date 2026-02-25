from __future__ import annotations

import re

from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_router import invoke_with_fallback

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def is_arabic_text(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def translate_to_english(text: str, provider_preference: str = "auto") -> str:
    """Translate arbitrary user text into English (best-effort).

    Used to improve retrieval when the corpus is primarily English while the user asks in Arabic.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a professional translator. Translate the user text into English.\n"
                "- Preserve names, numbers, units, and acronyms.\n"
                "- Keep it concise and faithful.\n"
                '- Output ONLY the English translation (no quotes, no commentary).',
            ),
            ("human", "{text}"),
        ]
    )

    translated, _provider = invoke_with_fallback(
        prompt,
        {"text": text},
        max_output_tokens=512,
        temperature=0.0,
        provider_preference=provider_preference,
    )

    # Defensive cleanup in case the model adds quotes or whitespace.
    translated = translated.strip().strip('"').strip("'").strip()
    return translated
