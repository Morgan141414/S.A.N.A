import pytest

from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskLevel, analyze_risk
from app.services.safety_checker import check_response_safety
from app.services.support_response import build_support_response


@pytest.mark.parametrize(
    "message",
    [
        "Меня бьют дома",
        "Мне опасно дома",
        "Взрослый трогал меня и заставляет молчать",
        "I am unsafe at home",
        "An adult touches me and told me don't tell anyone",
    ],
)
def test_minor_safety_cases_do_not_use_ordinary_minor_support(message: str) -> None:
    assessment = analyze_risk(message)
    mode = route_policy(assessment, age=15)

    assert assessment.level in {RiskLevel.MEDIUM, RiskLevel.HIGH}
    assert mode == ConversationMode.MINOR_SAFETY


def test_minor_safety_response_encourages_safe_adult_or_emergency_help() -> None:
    assessment = analyze_risk("Меня бьют дома")
    mode = route_policy(assessment, age=13)
    response = build_support_response(
        message="Меня бьют дома",
        risk_assessment=assessment,
        conversation_mode=mode,
        age=13,
    )
    safety_check = check_response_safety(response, assessment, mode)

    assert safety_check.passed
    assert "безопасному взрослому" in response
    assert "экстренной службе" in response
    assert "физической безопасности" in response
    assert "скрывать" in response
    assert "это останется между нами" not in response.casefold()
