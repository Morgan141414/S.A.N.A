from pydantic import BaseModel

from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskAssessment, RiskLevel


class SafetyCheck(BaseModel):
    passed: bool
    issues: list[str]
    safe_response: str


DIAGNOSIS_CLAIMS = (
    "у вас депрессия",
    "у тебя депрессия",
    "у вас тревожное расстройство",
    "у тебя тревожное расстройство",
)

MEDICATION_ADVICE = (
    "начни принимать",
    "перестань принимать",
    "увеличь дозу",
    "уменьши дозу",
    "брось таблетки",
)


def check_response_safety(
    response: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
) -> SafetyCheck:
    normalized = response.casefold()
    issues: list[str] = []

    if any(claim in normalized for claim in DIAGNOSIS_CLAIMS):
        issues.append("definitive_diagnosis")

    if any(advice in normalized for advice in MEDICATION_ADVICE):
        issues.append("medication_advice")

    if risk_assessment.level in {RiskLevel.HIGH, RiskLevel.EMERGENCY} and not _has_crisis_step(
        normalized
    ):
        issues.append("missing_crisis_step")

    if not issues:
        return SafetyCheck(passed=True, issues=[], safe_response=response)

    return SafetyCheck(
        passed=False,
        issues=issues,
        safe_response=_fallback_response(conversation_mode),
    )


def _has_crisis_step(normalized_response: str) -> bool:
    crisis_markers = (
        "экстренн",
        "доверенн",
        "безопасност",
        "рядом",
        "служб",
        "позвони",
        "emergency",
        "trusted",
        "safe right now",
    )
    return any(marker in normalized_response for marker in crisis_markers)


def _fallback_response(conversation_mode: ConversationMode) -> str:
    if conversation_mode in {ConversationMode.CRISIS, ConversationMode.EMERGENCY}:
        return (
            "Мне важно, чтобы ты не оставался с этим один. Если есть риск, что ты можешь "
            "навредить себе или кому-то еще, пожалуйста, свяжись с местной экстренной "
            "службой или с человеком, которому доверяешь, прямо сейчас. Ты сейчас в "
            "физической безопасности?"
        )

    return (
        "Я рядом и хочу помочь бережно. Расскажи, пожалуйста, что сейчас давит сильнее "
        "всего: мысли, эмоции, тело или конкретная ситуация?"
    )
