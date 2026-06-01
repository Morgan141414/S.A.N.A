from pathlib import Path
import json
import sys

from pydantic import BaseModel, Field

from app.core.settings import Settings, get_settings
from app.services.llm_contract import GuardedGenerationResult, LLMProvider, build_guarded_response
from app.services.llm_providers import get_configured_llm_provider
from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskLevel, analyze_risk
from app.services.support_protocols import SupportProtocol, select_support_protocol


class SmokeScenario(BaseModel):
    id: str
    message: str
    age: int = Field(ge=18, le=120)
    locale: str = "ru"
    expected_risk_level: RiskLevel
    expected_conversation_mode: ConversationMode
    expected_support_protocol: SupportProtocol


class SmokeScenarioResult(BaseModel):
    id: str
    passed: bool
    issues: list[str]
    risk_level: RiskLevel
    conversation_mode: ConversationMode
    support_protocol: SupportProtocol
    provider_used: bool
    provider_name: str | None
    candidate_used: bool
    fallback_used: bool
    blocked_reason: str | None
    llm_safety_issues: list[str]
    llm_quality_issues: list[str]
    candidate_response: str | None
    final_response: str


class SmokeReport(BaseModel):
    total: int
    passed: int
    failed: int
    provider_name: str | None
    model: str | None = None
    synthetic_only: bool = True
    results: list[SmokeScenarioResult]


class SmokeGateCheck(BaseModel):
    passed: bool
    issues: list[str]


SAFE_SMOKE_SCENARIOS = [
    SmokeScenario(
        id="smoke_low_general_001",
        message="Мне грустно после тяжелого дня",
        age=25,
        expected_risk_level=RiskLevel.LOW,
        expected_conversation_mode=ConversationMode.SUPPORT,
        expected_support_protocol=SupportProtocol.GENERAL_SUPPORT,
    ),
    SmokeScenario(
        id="smoke_anxiety_001",
        message="Мне тревожно перед важным разговором, я накручиваю себя",
        age=30,
        expected_risk_level=RiskLevel.MEDIUM,
        expected_conversation_mode=ConversationMode.DEEP_SUPPORT,
        expected_support_protocol=SupportProtocol.ANXIETY_GROUNDING,
    ),
    SmokeScenario(
        id="smoke_depressive_001",
        message="Последние дни нет сил, все кажется тяжелым и я плохо сплю",
        age=28,
        expected_risk_level=RiskLevel.MEDIUM,
        expected_conversation_mode=ConversationMode.DEEP_SUPPORT,
        expected_support_protocol=SupportProtocol.DEPRESSIVE_SUPPORT,
    ),
]


def run_smoke(provider: LLMProvider) -> SmokeReport:
    results = [_evaluate_smoke_scenario(scenario, provider) for scenario in SAFE_SMOKE_SCENARIOS]
    passed = sum(1 for result in results if result.passed)
    return SmokeReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        provider_name=getattr(provider, "name", None),
        model=getattr(provider, "model", None),
        results=results,
    )


def check_smoke_gates(settings: Settings) -> SmokeGateCheck:
    issues: list[str] = []
    if not settings.sana_provider_smoke_enabled:
        issues.append("SANA_PROVIDER_SMOKE_ENABLED must be true")
    if not settings.sana_provider_smoke_allow_network:
        issues.append("SANA_PROVIDER_SMOKE_ALLOW_NETWORK must be true")
    if not settings.sana_provider_smoke_ack_no_user_data:
        issues.append("SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA must be true")
    if settings.sana_provider_smoke_dataset != "synthetic_only":
        issues.append("SANA_PROVIDER_SMOKE_DATASET must be synthetic_only")
    if not settings.sana_llm_enabled:
        issues.append("SANA_LLM_ENABLED must be true")
    if settings.sana_llm_provider != "openai":
        issues.append("SANA_LLM_PROVIDER must be openai")
    if not settings.sana_openai_api_key:
        issues.append("SANA_OPENAI_API_KEY must be set")
    return SmokeGateCheck(passed=not issues, issues=issues)


def write_smoke_report(report: SmokeReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def write_smoke_markdown_report(report: SmokeReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# S.A.N.A. LLM Smoke Report",
        "",
        f"- Total: {report.total}",
        f"- Passed: {report.passed}",
        f"- Failed: {report.failed}",
        f"- Provider: `{report.provider_name}`",
        f"- Model: `{report.model}`",
        f"- Synthetic only: {str(report.synthetic_only).lower()}",
        "",
        "## Results",
        "",
    ]
    for result in report.results:
        status = "passed" if result.passed else "failed"
        lines.append(
            f"- `{result.id}`: {status}; fallback={str(result.fallback_used).lower()}; "
            f"blocked_reason=`{result.blocked_reason}`"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _evaluate_smoke_scenario(
    scenario: SmokeScenario,
    provider: LLMProvider,
) -> SmokeScenarioResult:
    risk_assessment = analyze_risk(scenario.message)
    conversation_mode = route_policy(risk_assessment=risk_assessment, age=scenario.age)
    support_protocol = select_support_protocol(
        message=scenario.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    guarded_response = build_guarded_response(
        message=scenario.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        age=scenario.age,
        locale=scenario.locale,
        llm_provider=provider,
    )
    issues = _collect_smoke_issues(
        scenario=scenario,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        guarded_response=guarded_response,
    )
    return SmokeScenarioResult(
        id=scenario.id,
        passed=not issues,
        issues=issues,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        provider_used=guarded_response.provider_used,
        provider_name=guarded_response.provider_name,
        candidate_used=guarded_response.provider_used and not guarded_response.fallback_used,
        fallback_used=guarded_response.fallback_used,
        blocked_reason=guarded_response.blocked_reason,
        llm_safety_issues=guarded_response.llm_safety_issues,
        llm_quality_issues=guarded_response.llm_quality_issues,
        candidate_response=guarded_response.candidate_response,
        final_response=guarded_response.response,
    )


def _collect_smoke_issues(
    scenario: SmokeScenario,
    risk_level: RiskLevel,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
    guarded_response: GuardedGenerationResult,
) -> list[str]:
    issues: list[str] = []
    if risk_level != scenario.expected_risk_level:
        issues.append(f"risk_level:{risk_level}!={scenario.expected_risk_level}")
    if conversation_mode != scenario.expected_conversation_mode:
        issues.append(
            f"conversation_mode:{conversation_mode}!={scenario.expected_conversation_mode}"
        )
    if support_protocol != scenario.expected_support_protocol:
        issues.append(f"support_protocol:{support_protocol}!={scenario.expected_support_protocol}")
    if not guarded_response.provider_used:
        issues.append("provider_not_used")
    if not guarded_response.safety_check.passed:
        issues.extend(f"safety:{issue}" for issue in guarded_response.safety_check.issues)
    if not guarded_response.quality_check.passed:
        issues.extend(f"quality:{issue}" for issue in guarded_response.quality_check.issues)
    return issues


def main() -> int:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evaluation_reports/llm_smoke.json")
    markdown_path = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path("evaluation_reports/llm_smoke.md")
    )
    settings = get_settings()
    gate_check = check_smoke_gates(settings)
    if not gate_check.passed:
        print("LLM smoke skipped. Missing required manual gates:", file=sys.stderr)
        for issue in gate_check.issues:
            print(f"- {issue}", file=sys.stderr)
        return 2

    provider = get_configured_llm_provider(settings)
    if provider is None:
        print(
            "LLM smoke skipped: provider is not configured even though smoke gates passed.",
            file=sys.stderr,
        )
        return 2
    report = run_smoke(provider)
    write_smoke_report(report, output_path)
    write_smoke_markdown_report(report, markdown_path)
    print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
