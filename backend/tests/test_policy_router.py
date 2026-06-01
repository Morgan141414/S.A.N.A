from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskLevel, analyze_risk


def test_emergency_routes_to_emergency() -> None:
    assessment = analyze_risk("У меня есть план")

    assert assessment.level == RiskLevel.EMERGENCY
    assert route_policy(assessment, age=16) == ConversationMode.EMERGENCY


def test_high_risk_routes_to_crisis_even_for_minor() -> None:
    assessment = analyze_risk("Я не хочу жить")

    assert assessment.level == RiskLevel.HIGH
    assert route_policy(assessment, age=15) == ConversationMode.CRISIS


def test_medium_adult_routes_to_deep_support() -> None:
    assessment = analyze_risk("У меня тревога и я не могу спать")

    assert assessment.level == RiskLevel.MEDIUM
    assert route_policy(assessment, age=30) == ConversationMode.DEEP_SUPPORT


def test_low_minor_routes_to_minor_support() -> None:
    assessment = analyze_risk("Мне грустно после школы")

    assert assessment.level == RiskLevel.LOW
    assert route_policy(assessment, age=14) == ConversationMode.MINOR_SUPPORT


def test_minor_abuse_routes_to_minor_safety() -> None:
    assessment = analyze_risk("Меня бьют дома и мне страшно")

    assert assessment.level in {RiskLevel.MEDIUM, RiskLevel.HIGH}
    assert route_policy(assessment, age=14) == ConversationMode.MINOR_SAFETY


def test_low_adult_routes_to_support() -> None:
    assessment = analyze_risk("Мне грустно после сложного дня")

    assert assessment.level == RiskLevel.LOW
    assert route_policy(assessment, age=30) == ConversationMode.SUPPORT
