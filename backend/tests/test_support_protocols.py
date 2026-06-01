import pytest

from app.services.policy_router import route_policy
from app.services.risk_classifier import analyze_risk
from app.services.support_protocols import SupportProtocol, select_support_protocol
from app.services.support_response import build_support_response


@pytest.mark.parametrize(
    ("message", "expected_protocol", "expected_phrase"),
    [
        ("У меня паническая атака и я задыхаюсь", SupportProtocol.PANIC_GROUNDING, "пять предметов"),
        ("У меня тревожно и я не могу спать", SupportProtocol.ANXIETY_GROUNDING, "факты"),
        ("У меня депрессия и нет сил", SupportProtocol.DEPRESSIVE_SUPPORT, "маленький шаг"),
        ("Мне одиноко после расставания", SupportProtocol.GRIEF_LONELINESS, "одиноко"),
        ("У меня конфликт на работе и стресс", SupportProtocol.CONFLICT_STRESS, "безопасным"),
    ],
)
def test_v0_2_support_protocol_responses(
    message: str,
    expected_protocol: SupportProtocol,
    expected_phrase: str,
) -> None:
    assessment = analyze_risk(message)
    mode = route_policy(assessment, age=25)
    protocol = select_support_protocol(message, assessment, mode)
    response = build_support_response(message, assessment, mode, protocol, age=25)

    assert protocol == expected_protocol
    assert expected_phrase in response
    assert "не могу ставить диагноз" in response or protocol in {
        SupportProtocol.GRIEF_LONELINESS,
        SupportProtocol.CONFLICT_STRESS,
    }


def test_crisis_protocol_overrides_content_protocol() -> None:
    assessment = analyze_risk("Я не хочу жить, у меня паника")
    mode = route_policy(assessment, age=25)

    assert select_support_protocol("Я не хочу жить, у меня паника", assessment, mode) == (
        SupportProtocol.CRISIS
    )
