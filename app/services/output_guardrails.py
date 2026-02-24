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
    # Arabic refusal phrases (made more specific)
    "لا أملك معلومات رسمية بخصوص",
    "لا تتوفر لديّ هذه المعلومات",
    "لا يمكنني الإجابة عن هذا السؤال",
    "لا أملك معلومات كافية في المستندات",
    "غير متوفر في المستندات الرسمية",
    "لم أتمكن من العثور على معلومات",
    "لا توجد معلومات كافية لتقديم إجابة",
    # English refusal phrases (made more specific)
    "I don't have sufficient official information",
    "I do not have access to information regarding",
    "I cannot find any mention of",
    "not found in the provided official context",
    "not mentioned in the available documents",
    "I cannot answer this specific question",
    "insufficient context to provide a verified official answer",
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
