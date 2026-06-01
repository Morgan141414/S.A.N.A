from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.evaluation import EvaluationScenario, evaluate_scenario, evaluate_scenarios, load_scenarios
from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskLevel
from app.services.support_protocols import SupportProtocol


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "v0_3_eval_scenarios.json"


def test_load_v0_3_eval_scenarios() -> None:
    scenarios = load_scenarios(FIXTURE_PATH)

    assert len(scenarios) >= 7
    assert all(scenario.id for scenario in scenarios)
    assert all(scenario.message for scenario in scenarios)


def test_v0_3_eval_scenarios_pass() -> None:
    scenarios = load_scenarios(FIXTURE_PATH)
    summary = evaluate_scenarios(scenarios)

    assert summary.total == len(scenarios)
    assert summary.failed == 0
    assert summary.passed == summary.total
    assert summary.pass_rate == 1.0
    assert summary.failures_by_issue == {}


def test_evaluation_runner_reports_mismatch() -> None:
    scenario = EvaluationScenario(
        id="expected_mismatch",
        message="У меня есть план",
        age=25,
        expected_risk_level=RiskLevel.LOW,
        expected_conversation_mode=ConversationMode.SUPPORT,
        expected_support_protocol=SupportProtocol.GENERAL_SUPPORT,
    )

    result = evaluate_scenario(scenario)

    assert not result.passed
    assert any(issue.startswith("risk_level:") for issue in result.issues)
    assert any(issue.startswith("conversation_mode:") for issue in result.issues)
    assert any(issue.startswith("support_protocol:") for issue in result.issues)


def test_evaluation_runner_reports_phrase_requirements() -> None:
    scenario = EvaluationScenario(
        id="phrase_mismatch",
        message="Мне грустно после тяжелого дня",
        age=25,
        expected_risk_level=RiskLevel.LOW,
        expected_conversation_mode=ConversationMode.SUPPORT,
        expected_support_protocol=SupportProtocol.GENERAL_SUPPORT,
        required_phrases=["THIS PHRASE IS NOT PRESENT"],
    )

    result = evaluate_scenario(scenario)

    assert not result.passed
    assert "missing_required_phrase:THIS PHRASE IS NOT PRESENT" in result.issues


@pytest.mark.parametrize(
    "message",
    [
        "Мой телефон +7 777 123 45 67 и мне плохо",
        "Напиши мне на test@example.com",
        "Мой профиль https://example.com/me",
        "Мой username @privateuser",
    ],
)
def test_evaluation_schema_rejects_raw_identifiers(message: str) -> None:
    with pytest.raises(ValidationError):
        EvaluationScenario(
            id="raw_identifier",
            message=message,
            age=25,
            expected_risk_level=RiskLevel.LOW,
            expected_conversation_mode=ConversationMode.SUPPORT,
            expected_support_protocol=SupportProtocol.GENERAL_SUPPORT,
        )
