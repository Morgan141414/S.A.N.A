from pydantic import BaseModel

from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskAssessment, RiskLevel


class SafetyCheck(BaseModel):
    passed: bool
    issues: list[str]
    safe_response: str


DIAGNOSIS_CLAIMS = (
    "это биполярное расстройство",
    "это птср",
    "у вас депрессия",
    "у тебя депрессия",
    "у тебя птср",
    "у вас тревожное расстройство",
    "у тебя тревожное расстройство",
    "you have depression",
    "you have ptsd",
    "you have bipolar",
)

MEDICATION_ADVICE = (
    "начни принимать",
    "перестань принимать",
    "увеличь дозу",
    "уменьши дозу",
    "брось таблетки",
    "можешь принять феназепам",
    "прекрати пить антидепрессанты",
    "take xanax",
    "stop antidepressants",
    "double your dose",
)

FALSE_SAFETY_CLAIMS = (
    "ты в безопасности",
    "вы в безопасности",
    "все точно будет хорошо",
    "ничего не случится",
    "you are safe",
    "everything will be fine",
    "nothing bad will happen",
)

SECRECY_OR_CONFIDENTIALITY_TRAPS = (
    "это останется между нами",
    "никому не говори",
    "не рассказывай никому",
    "keep this secret",
    "don't tell anyone",
    "do not tell anyone",
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

    if any(claim in normalized for claim in FALSE_SAFETY_CLAIMS):
        issues.append("false_safety_claim")

    if any(trap in normalized for trap in SECRECY_OR_CONFIDENTIALITY_TRAPS):
        issues.append("secrecy_or_confidentiality_trap")

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
    return _has_immediate_action(normalized_response) and _has_direct_safety_check(
        normalized_response
    )


def _has_immediate_action(normalized_response: str) -> bool:
    action_markers = (
        "экстренн",
        "доверенн",
        "служб",
        "позвони",
        "позови",
        "свяжись",
        "кризис",
        "emergency",
        "crisis",
        "trusted",
    )
    return any(marker in normalized_response for marker in action_markers)


def _has_direct_safety_check(normalized_response: str) -> bool:
    safety_check_markers = (
        "физической безопасности",
        "ты сейчас в безопасности",
        "ты в физической безопасности",
        "are you physically safe",
        "safe right now",
    )
    return any(marker in normalized_response for marker in safety_check_markers)


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
