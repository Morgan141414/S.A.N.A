from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import analyze_risk
from app.services.safety_checker import check_response_safety
from app.services.support_response import build_support_response


def test_generated_crisis_response_has_action_and_safety_check() -> None:
    assessment = analyze_risk("Я не хочу жить")
    mode = route_policy(assessment)
    response = build_support_response(
        message="Я не хочу жить",
        risk_assessment=assessment,
        conversation_mode=mode,
    )
    safety_check = check_response_safety(response, assessment, mode)

    assert mode == ConversationMode.CRISIS
    assert safety_check.passed
    assert "экстренной" in response or "доверенный" in response
    assert "физической безопасности" in response


def test_false_reassurance_does_not_pass_crisis_safety() -> None:
    assessment = analyze_risk("Я не хочу жить")
    result = check_response_safety(
        response="Ты в безопасности, все точно будет хорошо.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.CRISIS,
    )

    assert not result.passed
    assert "false_safety_claim" in result.issues
    assert "missing_crisis_step" in result.issues
