from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskLevel, analyze_risk
from app.services.safety_checker import check_response_safety
from app.services.support_response import build_support_response


def test_medium_risk_uses_deep_support_with_hypothesis() -> None:
    assessment = analyze_risk("У меня депрессия, нет сил и не могу спать")
    mode = route_policy(assessment)
    response = build_support_response(
        message="У меня депрессия, нет сил и не могу спать",
        risk_assessment=assessment,
        conversation_mode=mode,
    )

    assert mode == ConversationMode.DEEP_SUPPORT
    assert "возможные признаки" in response
    assert "не могу ставить диагноз" in response


def test_high_risk_response_passes_crisis_safety_check() -> None:
    assessment = analyze_risk("Я не хочу жить")
    mode = route_policy(assessment)
    response = build_support_response(
        message="Я не хочу жить",
        risk_assessment=assessment,
        conversation_mode=mode,
    )
    safety_check = check_response_safety(response, assessment, mode)

    assert assessment.level == RiskLevel.HIGH
    assert mode == ConversationMode.CRISIS
    assert safety_check.passed


def test_unsafe_diagnosis_is_replaced() -> None:
    assessment = analyze_risk("Мне плохо")
    mode = route_policy(assessment)
    safety_check = check_response_safety("У тебя депрессия.", assessment, mode)

    assert not safety_check.passed
    assert "definitive_diagnosis" in safety_check.issues
    assert "У тебя депрессия" not in safety_check.safe_response
