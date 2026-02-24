from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

# نعتمد على الإشارة المباشرة من النظام فقط لمنع الحجب الخاطئ
LLM_REFUSAL_SIGNALS = [
    "HITL_ESCALATION_REQUIRED"
]

OUTPUT_SAFETY_BLOCKLIST = [
    "bomb", "weapon", "kill", "attack", "hack",
    "قنبلة", "سلاح", "اغتيال", "قرصنة",
]

MIN_ANSWER_LENGTH = 15

@dataclass
class OutputGuardResult:
    should_escalate: bool
    reason: str

def check_output(answer: str, citations_available: bool = False) -> OutputGuardResult:
    for signal in LLM_REFUSAL_SIGNALS:
        if signal in answer:
            logger.warning("Output guardrail: LLM refusal detected — '%s'", signal)
            return OutputGuardResult(should_escalate=True, reason=f"llm_refusal:{signal}")

    if len(answer.strip()) < MIN_ANSWER_LENGTH:
        logger.warning("Output guardrail: Answer too short (%d chars)", len(answer.strip()))
        return OutputGuardResult(should_escalate=True, reason="answer_too_short")

    answer_lower = answer.lower()
    for term in OUTPUT_SAFETY_BLOCKLIST:
        if term in answer_lower:
            logger.error("Output guardrail: SAFETY BLOCK — blocked term '%s' in answer", term)
            return OutputGuardResult(should_escalate=True, reason=f"safety_block:{term}")

    return OutputGuardResult(should_escalate=False, reason="passed")