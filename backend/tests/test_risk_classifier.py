import pytest

from app.services.risk_classifier import RiskLevel, analyze_risk, classify_risk


def test_low_risk_message() -> None:
    assert classify_risk("Мне грустно и я устал") == RiskLevel.LOW


def test_medium_risk_message() -> None:
    assert classify_risk("У меня тревога и я не могу спать") == RiskLevel.MEDIUM


def test_high_risk_message() -> None:
    assert classify_risk("Я не хочу жить") == RiskLevel.HIGH


def test_emergency_message() -> None:
    assert classify_risk("У меня есть план и я сделаю это прямо сейчас") == RiskLevel.EMERGENCY


@pytest.mark.parametrize(
    ("message", "expected_level"),
    [
        ("Мне грустно после тяжелого дня", RiskLevel.LOW),
        ("У меня anxiety and I can't sleep", RiskLevel.MEDIUM),
        ("I want to die", RiskLevel.HIGH),
        ("I have a plan tonight", RiskLevel.EMERGENCY),
    ],
)
def test_multilingual_risk_matrix(message: str, expected_level: RiskLevel) -> None:
    assert classify_risk(message) == expected_level


def test_risk_assessment_contains_score_and_terms() -> None:
    assessment = analyze_risk("У меня тревога и я не могу спать")

    assert assessment.level == RiskLevel.MEDIUM
    assert assessment.score >= 0.30
    assert "тревог" in assessment.matched_terms


def test_immediate_plan_overrides_score() -> None:
    assessment = analyze_risk("У меня есть план")

    assert assessment.level == RiskLevel.EMERGENCY
    assert assessment.score == 1.0
    assert assessment.features.immediate_plan == 0.5
