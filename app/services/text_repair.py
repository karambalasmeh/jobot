from __future__ import annotations

import re
from typing import Optional


_MOJIBAKE_MARKERS = (
    "Ø",
    "Ù",
    "Ã",
    "Â",
    "â",  # often appears with smart quotes / dashes when mis-decoded
)


def _looks_like_mojibake(text: str) -> bool:
    # Heuristic: Arabic UTF-8 bytes mis-decoded as Windows-1252 often contain these characters.
    return any(m in text for m in _MOJIBAKE_MARKERS)


def repair_utf8_mojibake_cp1252(text: str) -> str:
    """Best-effort repair for UTF-8 text that was mistakenly decoded as cp1252 and stored as Unicode.

    Example: "Ù…Ø­Ø§Ø¯Ø«Ø© Ø¬Ø¯ÙŠØ¯Ø©" -> "محادثة جديدة"
    """
    if not text or not _looks_like_mojibake(text):
        return text

    try:
        fixed = text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

    # Only accept the repair if it produces plausible Arabic (or removes the mojibake markers).
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", fixed))
    if arabic_chars > 0 and not _looks_like_mojibake(fixed):
        return fixed

    # If it didn't produce Arabic but removed the marker patterns, it's still likely an improvement.
    if _looks_like_mojibake(text) and not _looks_like_mojibake(fixed):
        return fixed

    return text


def repair_optional(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return repair_utf8_mojibake_cp1252(text)

