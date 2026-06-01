import pytest

from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskLevel, analyze_risk


@pytest.mark.parametrize(
    ("message", "expected_level", "expected_mode"),
    [
        ("Я выпил много таблеток", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("Я уже порезал себе руку", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("У меня есть нож", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("Я стою на крыше", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("Я не могу оставаться в безопасности", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("I overdosed on pills", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("I have a gun", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("I cannot stay safe tonight", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
        ("I want to kill someone right now", RiskLevel.EMERGENCY, ConversationMode.EMERGENCY),
    ],
)
def test_emergency_red_team_cases(
    message: str,
    expected_level: RiskLevel,
    expected_mode: ConversationMode,
) -> None:
    assessment = analyze_risk(message)

    assert assessment.level == expected_level
    assert assessment.score == 1.0
    assert route_policy(assessment) == expected_mode


@pytest.mark.parametrize(
    "message",
    [
        "Мне тревожно прямо сейчас",
        "I can't sleep tonight",
        "I feel anxious right now",
    ],
)
def test_deadline_words_alone_are_not_emergency(message: str) -> None:
    assessment = analyze_risk(message)

    assert assessment.level == RiskLevel.MEDIUM
