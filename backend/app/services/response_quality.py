from pydantic import BaseModel

from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskLevel
from app.services.support_protocols import SupportProtocol


class ResponseQualityCheck(BaseModel):
    passed: bool
    issues: list[str]


EMPATHY_MARKERS = (
    "я рядом",
    "похоже",
    "спасибо",
    "слышу",
    "важно",
    "может быть",
)

NEXT_STEP_MARKERS = (
    "попробуй",
    "назови",
    "выберем",
    "обратись",
    "свяжись",
    "позови",
    "напиши",
    "шаг",
)

QUESTION_MARKERS = ("?",)


def check_response_quality(
    response: str,
    risk_level: RiskLevel,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
) -> ResponseQualityCheck:
    normalized = response.casefold()
    issues: list[str] = []

    if not any(marker in normalized for marker in EMPATHY_MARKERS):
        issues.append("missing_empathic_reflection")

    if not any(marker in normalized for marker in NEXT_STEP_MARKERS):
        issues.append("missing_next_step")

    if not any(marker in response for marker in QUESTION_MARKERS):
        issues.append("missing_focused_question")

    if conversation_mode in {ConversationMode.CRISIS, ConversationMode.EMERGENCY}:
        word_count = len(response.split())
        if word_count > 90:
            issues.append("crisis_response_too_long")
        if "физической безопасности" not in normalized and "physically safe" not in normalized:
            issues.append("missing_direct_safety_check")

    if support_protocol == SupportProtocol.DEPRESSIVE_SUPPORT:
        if "навредить себе" not in normalized and "не жить" not in normalized:
            issues.append("missing_self_harm_screen")

    if support_protocol == SupportProtocol.PANIC_GROUNDING:
        medical_markers = ("боль в груди", "обморок", "сильная одышка", "риск навредить")
        if not any(marker in normalized for marker in medical_markers):
            issues.append("missing_panic_medical_red_flag_check")

    return ResponseQualityCheck(passed=not issues, issues=issues)

