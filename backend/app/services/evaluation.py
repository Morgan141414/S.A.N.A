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

    scenario_by_id = {scenario.id: scenario for scenario in scenarios}
    for result in results:
        if result.passed:
            continue
        for issue in result.issues:
            failures_by_issue[issue] = failures_by_issue.get(issue, 0) + 1
        for tag in scenario_by_id[result.id].tags:
            failures_by_tag[tag] = failures_by_tag.get(tag, 0) + 1

    return EvaluationSummary(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        pass_rate=round(passed / len(results), 4) if results else 0.0,
        failures_by_issue=failures_by_issue,
        failures_by_tag=failures_by_tag,
        results=results,
    )


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


def main() -> int:
    default_path = (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "v0_3_eval_scenarios.json"
    )
    scenario_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    summary = evaluate_scenarios(load_scenarios(scenario_path))
    print(summary.model_dump_json(indent=2))
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
