from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.training_manifest import (
    TrainingGate,
    TrainingMethod,
    TrainingRunManifest,
    TrainingRunStatus,
    build_training_dry_run_report,
    build_draft_training_manifest,
    load_training_manifest,
    write_training_dry_run_markdown,
    write_training_dry_run_report,
    write_training_manifest,
)
from app.services.evaluation import InstructionTrainingExample, ReviewDecision, ScenarioSourceType
from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskLevel
from app.services.support_protocols import SupportProtocol


def test_draft_training_manifest_is_blocked_until_readiness() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )

    assert manifest.status == TrainingRunStatus.BLOCKED_UNTIL_READINESS
    assert manifest.method == TrainingMethod.QLORA
    assert TrainingGate.NO_CRISIS_EMERGENCY_MINOR in manifest.required_gates
    assert manifest.allowed_risk_levels == ["low", "medium"]
    assert "crisis" in manifest.forbidden_conversation_modes
    assert "safety_failure_count" in manifest.metrics_to_compare


def test_training_manifest_requires_all_safety_gates() -> None:
    with pytest.raises(ValidationError, match="missing required gates"):
        TrainingRunManifest(
            run_id="unsafe_manifest",
            base_model="llama3.1:8b",
            method=TrainingMethod.QLORA,
            dataset_path="evaluation_reports/approved_instruction_examples.json",
            output_dir="training_runs/unsafe_manifest",
            status=TrainingRunStatus.READY_FOR_TRAINING,
            required_gates=[TrainingGate.APPROVED_LOW_MEDIUM_ONLY],
        )


def test_training_manifest_can_be_written_and_loaded(tmp_path: Path) -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )
    output_path = tmp_path / "training_manifest.json"

    write_training_manifest(manifest, output_path)
    loaded = load_training_manifest(output_path)

    assert loaded == manifest
    assert '"status": "blocked_until_readiness"' in output_path.read_text(encoding="utf-8")


def test_training_dry_run_report_is_blocked_until_readiness() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )
    examples = [
        InstructionTrainingExample(
            id="safe_review_case",
            dataset_version="v0.4.0",
            source_type=ScenarioSourceType.CLINICIAN_AUTHORED,
            locale="ru",
            user_message="Мне тревожно перед встречей",
            assistant_response="Я рядом. Давай начнем с одного спокойного шага.",
            risk_level=RiskLevel.LOW,
            conversation_mode=ConversationMode.SUPPORT,
            support_protocol=SupportProtocol.GENERAL_SUPPORT,
            reviewer_decision=ReviewDecision.APPROVED,
        )
    ]

    report = build_training_dry_run_report(manifest=manifest, examples=examples)

    assert report.blocked
    assert report.dataset_total == 1
    assert report.train_examples == 1
    assert report.validation_examples == 0
    assert report.estimated_optimizer_steps == 1
    assert "manifest_blocked_until_readiness" in report.blocking_reasons
    assert "validation_split_disabled_for_single_example" in report.warnings


def test_training_dry_run_blocks_empty_or_forbidden_dataset() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )
    crisis_example = InstructionTrainingExample(
        id="crisis_case",
        dataset_version="v0.4.0",
        source_type=ScenarioSourceType.RED_TEAM,
        locale="ru",
        user_message="Я не хочу жить",
        assistant_response="Позвони в экстренную службу прямо сейчас.",
        risk_level=RiskLevel.HIGH,
        conversation_mode=ConversationMode.CRISIS,
        support_protocol=SupportProtocol.CRISIS,
        reviewer_decision=ReviewDecision.APPROVED,
    )

    empty_report = build_training_dry_run_report(manifest=manifest, examples=[])
    crisis_report = build_training_dry_run_report(manifest=manifest, examples=[crisis_example])

    assert "dataset_empty" in empty_report.blocking_reasons
    assert "forbidden_risk_level:crisis_case:high" in crisis_report.blocking_reasons
    assert "forbidden_conversation_mode:crisis_case:crisis" in crisis_report.blocking_reasons


def test_training_dry_run_reports_can_be_written(tmp_path: Path) -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )
    report = build_training_dry_run_report(manifest=manifest, examples=[])
    json_path = tmp_path / "dry_run.json"
    markdown_path = tmp_path / "dry_run.md"

    write_training_dry_run_report(report, json_path)
    write_training_dry_run_markdown(report, markdown_path)

    assert '"dataset_empty"' in json_path.read_text(encoding="utf-8")
    assert "# S.A.N.A. Training Dry Run" in markdown_path.read_text(encoding="utf-8")
