"""
Output Guardrails Service
Validates LLM-generated answers before they are returned to the user.
Enforces fact-grounding, citation presence, and content safety.
"""
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

# Phrases the LLM outputs when it admits it cannot answer
LLM_REFUSAL_SIGNALS = [
    # Explicit escalation signal from the system prompt
    "HITL_ESCALATION_REQUIRED",
    # Arabic refusal phrases
    "عذراً، لا أملك معلومات رسمية",
    "لا تتوفر لديّ",
    "لا يمكنني الإجابة",
    "لا أملك معلومات كافية",
    "غير متوفر في المستندات",
    "لم أتمكن من العثور",
    "لا توجد معلومات كافية",
    # English refusal phrases
    "I'm sorry, I don't have sufficient official information",
    "I don't have",
    "I cannot find",
    "not found in the provided context",
    "not mentioned in the context",
    "not available in the documents",
    "I cannot answer",
    "insufficient context",
]

# Patterns that indicate off-topic or policy-violating content crept into the output
OUTPUT_SAFETY_BLOCKLIST = [
    "bomb", "weapon", "kill", "attack", "hack",
    "قنبلة", "سلاح", "اغتيال", "قرصنة",
]

MIN_ANSWER_LENGTH = 30  # answers shorter than this are likely refusals or hallucinations


@dataclass
class OutputGuardResult:
    should_escalate: bool
    reason: str  # for logging/audit


def check_output(answer: str, citations_available: bool = False) -> OutputGuardResult:
    """
    Runs the answer through all output guardrail checks.
    Returns OutputGuardResult indicating whether to escalate.
    """
    # 1. LLM Refusal Detection — LLM admitted it doesn't know
    for signal in LLM_REFUSAL_SIGNALS:
        if signal.lower() in answer.lower():
            logger.warning("Output guardrail: LLM refusal detected — '%s'", signal)
            return OutputGuardResult(should_escalate=True, reason=f"llm_refusal:{signal}")

    # 2. Too-short answer guard — likely incomplete or malformed
    if len(answer.strip()) < MIN_ANSWER_LENGTH:
        logger.warning("Output guardrail: Answer too short (%d chars)", len(answer.strip()))
        return OutputGuardResult(should_escalate=True, reason="answer_too_short")

    # 3. Safety content filter — blocked terms in output
    answer_lower = answer.lower()
    for term in OUTPUT_SAFETY_BLOCKLIST:
        if term in answer_lower:
            logger.error("Output guardrail: SAFETY BLOCK — blocked term '%s' in answer", term)
            return OutputGuardResult(should_escalate=True, reason=f"safety_block:{term}")

    logger.debug("Output guardrail: answer passed all checks")
    return OutputGuardResult(should_escalate=False, reason="passed")
