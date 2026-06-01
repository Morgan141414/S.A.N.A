from pathlib import Path
import json
import re
import sys

from pydantic import BaseModel, Field, field_validator

from app.services.policy_router import ConversationMode, route_policy
from app.services.response_quality import ResponseQualityCheck, check_response_quality
from app.services.risk_classifier import RiskLevel, analyze_risk
from app.services.safety_checker import SafetyCheck, check_response_safety
from app.services.support_protocols import SupportProtocol, select_support_protocol
from app.services.support_response import build_support_response


class EvaluationScenario(BaseModel):
    id: str
    message: str
    age: int | None = Field(default=None, ge=0, le=120)
    locale: str = "ru"
    expected_risk_level: RiskLevel
    expected_conversation_mode: ConversationMode
    expected_support_protocol: SupportProtocol
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def reject_raw_identifiers(cls, value: str) -> str:
        patterns = (
            r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
            r"https?://\S+",
            r"@\w{3,}",
            r"\+?\d[\d\s().-]{8,}\d",
        )
        if any(re.search(pattern, value) for pattern in patterns):
            raise ValueError("evaluation scenario message must not contain raw identifiers")
        return value


class ScenarioEvaluationResult(BaseModel):
    id: str
    passed: bool
    issues: list[str]
    risk_level: RiskLevel
    conversation_mode: ConversationMode
    support_protocol: SupportProtocol
    safety_check: SafetyCheck
    quality_check: ResponseQualityCheck
    response: str


class EvaluationSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    failures_by_issue: dict[str, int]
    failures_by_tag: dict[str, int]
    coverage_by_risk_level: dict[str, int]
    coverage_by_conversation_mode: dict[str, int]
    coverage_by_support_protocol: dict[str, int]
    coverage_by_tag: dict[str, int]
    results: list[ScenarioEvaluationResult]


def load_scenarios(path: Path) -> list[EvaluationScenario]:
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    return [EvaluationScenario.model_validate(item) for item in raw_data]


def evaluate_scenario(scenario: EvaluationScenario) -> ScenarioEvaluationResult:
    risk_assessment = analyze_risk(scenario.message)
    conversation_mode = route_policy(risk_assessment=risk_assessment, age=scenario.age)
    support_protocol = select_support_protocol(
        message=scenario.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    response = build_support_response(
        message=scenario.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        age=scenario.age,
        locale=scenario.locale,
    )
    safety_check = check_response_safety(
        response=response,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    final_response = safety_check.safe_response
    quality_check = check_response_quality(
        response=final_response,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
    )

    issues = _collect_issues(
        scenario=scenario,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        safety_check=safety_check,
        quality_check=quality_check,
        response=final_response,
    )

    return ScenarioEvaluationResult(
        id=scenario.id,
        passed=not issues,
        issues=issues,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        safety_check=safety_check,
        quality_check=quality_check,
        response=final_response,
    )


def evaluate_scenarios(scenarios: list[EvaluationScenario]) -> EvaluationSummary:
    results = [evaluate_scenario(scenario) for scenario in scenarios]
    passed = sum(1 for result in results if result.passed)
    failures_by_issue: dict[str, int] = {}
    failures_by_tag: dict[str, int] = {}
    coverage_by_risk_level: dict[str, int] = {}
    coverage_by_conversation_mode: dict[str, int] = {}
    coverage_by_support_protocol: dict[str, int] = {}
    coverage_by_tag: dict[str, int] = {}

    scenario_by_id = {scenario.id: scenario for scenario in scenarios}
    for scenario in scenarios:
        _increment(coverage_by_risk_level, scenario.expected_risk_level.value)
        _increment(coverage_by_conversation_mode, scenario.expected_conversation_mode.value)
        _increment(coverage_by_support_protocol, scenario.expected_support_protocol.value)
        for tag in scenario.tags:
            _increment(coverage_by_tag, tag)

    for result in results:
        if result.passed:
            continue
        for issue in result.issues:
            _increment(failures_by_issue, issue)
        for tag in scenario_by_id[result.id].tags:
            _increment(failures_by_tag, tag)

    return EvaluationSummary(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        pass_rate=round(passed / len(results), 4) if results else 0.0,
        failures_by_issue=failures_by_issue,
        failures_by_tag=failures_by_tag,
        coverage_by_risk_level=coverage_by_risk_level,
        coverage_by_conversation_mode=coverage_by_conversation_mode,
        coverage_by_support_protocol=coverage_by_support_protocol,
        coverage_by_tag=coverage_by_tag,
        results=results,
    )


def write_evaluation_report(summary: EvaluationSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")


def write_markdown_report(summary: EvaluationSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# S.A.N.A. Evaluation Report",
        "",
        f"- Total: {summary.total}",
        f"- Passed: {summary.passed}",
        f"- Failed: {summary.failed}",
        f"- Pass rate: {summary.pass_rate}",
        "",
        "## Coverage By Risk Level",
        "",
        *_format_counter(summary.coverage_by_risk_level),
        "",
        "## Coverage By Conversation Mode",
        "",
        *_format_counter(summary.coverage_by_conversation_mode),
        "",
        "## Coverage By Support Protocol",
        "",
        *_format_counter(summary.coverage_by_support_protocol),
        "",
        "## Failures",
        "",
    ]
    if summary.failed == 0:
        lines.append("No failures.")
    else:
        for result in summary.results:
            if not result.passed:
                lines.append(f"- `{result.id}`: {', '.join(result.issues)}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _collect_issues(
    scenario: EvaluationScenario,
    risk_level: RiskLevel,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
    safety_check: SafetyCheck,
    quality_check: ResponseQualityCheck,
    response: str,
) -> list[str]:
    issues: list[str] = []
    normalized_response = response.casefold()

    if risk_level != scenario.expected_risk_level:
        issues.append(f"risk_level:{risk_level}!={scenario.expected_risk_level}")

    if conversation_mode != scenario.expected_conversation_mode:
        issues.append(
            f"conversation_mode:{conversation_mode}!={scenario.expected_conversation_mode}"
        )

    if support_protocol != scenario.expected_support_protocol:
        issues.append(f"support_protocol:{support_protocol}!={scenario.expected_support_protocol}")

    if not safety_check.passed:
        issues.extend(f"safety:{issue}" for issue in safety_check.issues)

    if not quality_check.passed:
        issues.extend(f"quality:{issue}" for issue in quality_check.issues)

    for phrase in scenario.required_phrases:
        if phrase.casefold() not in normalized_response:
            issues.append(f"missing_required_phrase:{phrase}")

    for phrase in scenario.forbidden_phrases:
        if phrase.casefold() in normalized_response:
            issues.append(f"forbidden_phrase:{phrase}")

    return issues


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _format_counter(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["No data."]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items())]


def main() -> int:
    default_path = (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "v0_3_eval_scenarios.json"
    )
    scenario_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    markdown_output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    summary = evaluate_scenarios(load_scenarios(scenario_path))
    if output_path is not None:
        write_evaluation_report(summary, output_path)
    if markdown_output_path is not None:
        write_markdown_report(summary, markdown_output_path)
    print(summary.model_dump_json(indent=2))
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
