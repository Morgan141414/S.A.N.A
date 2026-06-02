from pathlib import Path

from app.core.settings import get_settings
from app.services.llm_contract import MockLLMProvider
from app.services.llm_providers import LLMPreflightResult
from app.services.llm_smoke import (
    SAFE_SMOKE_SCENARIOS,
    check_provider_preflight,
    check_smoke_gates,
    run_smoke,
    write_smoke_markdown_report,
    write_smoke_report,
)


class PreflightProvider(MockLLMProvider):
    name = "preflight"

    def __init__(self, response: str, preflight_result: LLMPreflightResult) -> None:
        super().__init__(response)
        self._preflight_result = preflight_result

    def preflight(self) -> LLMPreflightResult:
        return self._preflight_result


def test_smoke_gates_reject_default_environment() -> None:
    gate_check = check_smoke_gates(get_settings({}))

    assert not gate_check.passed
    assert "SANA_PROVIDER_SMOKE_ENABLED must be true" in gate_check.issues
    assert "SANA_LLM_PROVIDER must be openai or ollama" in gate_check.issues


def test_smoke_gates_pass_only_with_explicit_manual_flags() -> None:
    gate_check = check_smoke_gates(
        get_settings(
            {
                "SANA_LLM_ENABLED": "true",
                "SANA_LLM_PROVIDER": "openai",
                "SANA_OPENAI_API_KEY": "test-key",
                "SANA_PROVIDER_SMOKE_ENABLED": "true",
                "SANA_PROVIDER_SMOKE_ALLOW_NETWORK": "true",
                "SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA": "true",
                "SANA_PROVIDER_SMOKE_DATASET": "synthetic_only",
            }
        )
    )

    assert gate_check.passed
    assert gate_check.issues == []


def test_smoke_gates_pass_for_ollama_without_api_key() -> None:
    gate_check = check_smoke_gates(
        get_settings(
            {
                "SANA_LLM_ENABLED": "true",
                "SANA_LLM_PROVIDER": "ollama",
                "SANA_LLM_MODEL": "llama3.1:8b",
                "SANA_PROVIDER_SMOKE_ENABLED": "true",
                "SANA_PROVIDER_SMOKE_ALLOW_NETWORK": "true",
                "SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA": "true",
                "SANA_PROVIDER_SMOKE_DATASET": "synthetic_only",
            }
        )
    )

    assert gate_check.passed
    assert gate_check.issues == []


def test_smoke_gates_reject_external_ollama_url() -> None:
    gate_check = check_smoke_gates(
        get_settings(
            {
                "SANA_LLM_ENABLED": "true",
                "SANA_LLM_PROVIDER": "ollama",
                "SANA_OLLAMA_BASE_URL": "https://example.com",
                "SANA_PROVIDER_SMOKE_ENABLED": "true",
                "SANA_PROVIDER_SMOKE_ALLOW_NETWORK": "true",
                "SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA": "true",
                "SANA_PROVIDER_SMOKE_DATASET": "synthetic_only",
            }
        )
    )

    assert not gate_check.passed
    assert (
        "SANA_OLLAMA_BASE_URL must be localhost or explicitly allowed private IP"
        in gate_check.issues
    )


def test_smoke_scenarios_are_adult_synthetic_low_or_medium() -> None:
    assert len(SAFE_SMOKE_SCENARIOS) >= 3
    assert all(scenario.age >= 18 for scenario in SAFE_SMOKE_SCENARIOS)
    assert all("@" not in scenario.message for scenario in SAFE_SMOKE_SCENARIOS)
    assert all("http" not in scenario.message for scenario in SAFE_SMOKE_SCENARIOS)


def test_provider_preflight_passes_when_provider_has_no_preflight() -> None:
    provider = MockLLMProvider("Я рядом. Что сейчас тяжелее всего?")

    result = check_provider_preflight(provider)

    assert result.passed
    assert result.issues == []


def test_provider_preflight_returns_provider_issues() -> None:
    provider = PreflightProvider(
        "Я рядом. Что сейчас тяжелее всего?",
        LLMPreflightResult(
            passed=False,
            provider_name="ollama",
            model="llama3.1:8b",
            issues=["ollama_model_missing"],
        ),
    )

    result = check_provider_preflight(provider)

    assert not result.passed
    assert result.issues == ["ollama_model_missing"]


def test_run_smoke_uses_provider_and_writes_reports(tmp_path: Path) -> None:
    provider = MockLLMProvider(
        "Я рядом. Похоже, тебе сейчас непросто. Попробуй назвать один маленький "
        "безопасный шаг на ближайшие 10 минут. Что сейчас давит сильнее всего?"
    )

    report = run_smoke(provider)

    assert report.total == len(SAFE_SMOKE_SCENARIOS)
    assert report.failed == 0
    assert report.provider_name == "mock"
    assert report.candidate_used_count == 2
    assert report.fallback_count == 1
    assert report.blocked_reasons == {"llm_quality_failed": 1}
    assert all(result.provider_used for result in report.results)
    assert all(result.final_response for result in report.results)

    json_path = tmp_path / "llm_smoke.json"
    markdown_path = tmp_path / "llm_smoke.md"
    write_smoke_report(report, json_path)
    write_smoke_markdown_report(report, markdown_path)

    assert '"synthetic_only":true' in json_path.read_text(encoding="utf-8").replace(" ", "")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "S.A.N.A. LLM Smoke Report" in markdown
    assert "Provider: `mock`" in markdown
    assert "Candidate used: 2" in markdown
    assert "Fallback used: 1" in markdown
    assert "- `llm_quality_failed`: 1" in markdown


def test_run_smoke_counts_blocked_reasons_for_fallbacks() -> None:
    provider = MockLLMProvider("У тебя депрессия. Все точно будет хорошо.")

    report = run_smoke(provider)

    assert report.candidate_used_count == 0
    assert report.fallback_count == len(SAFE_SMOKE_SCENARIOS)
    assert report.blocked_reasons == {"llm_safety_failed": len(SAFE_SMOKE_SCENARIOS)}
    assert all(result.blocked_reason == "llm_safety_failed" for result in report.results)


def test_smoke_markdown_report_includes_blocked_reason_breakdown(tmp_path: Path) -> None:
    provider = MockLLMProvider("У тебя депрессия. Все точно будет хорошо.")
    report = run_smoke(provider)
    markdown_path = tmp_path / "llm_smoke.md"

    write_smoke_markdown_report(report, markdown_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "## Blocked Reasons" in markdown
    assert "- `llm_safety_failed`: 3" in markdown
