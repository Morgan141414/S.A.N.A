from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.training_manifest import (
    TrainingGate,
    TrainingHardwareProfile,
    TrainingMethod,
    TrainingRunManifest,
    TrainingRunStatus,
    build_training_dry_run_report,
    build_draft_training_manifest,
    estimate_training_hardware,
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
    assert report.hardware_estimate.risk_level in {"low", "medium"}
    assert report.blocked_by_readiness
    assert not report.blocked_by_dataset_safety
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
    assert empty_report.blocked_by_dataset_safety
    assert "forbidden_risk_level:crisis_case:high" in crisis_report.blocking_reasons
    assert "forbidden_conversation_mode:crisis_case:crisis" in crisis_report.blocking_reasons
    assert crisis_report.blocked_by_dataset_safety


def test_training_hardware_estimate_marks_qlora_8b_on_8gb_as_tight() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )

    estimate = estimate_training_hardware(manifest)

    assert estimate.fits_gpu_memory
    assert estimate.risk_level in {"low", "medium"}
    assert any("8GB VRAM is a tight target" in note for note in estimate.notes)


def test_training_hardware_estimate_blocks_lora_8b_on_8gb() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_lora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_lora_001",
        method=TrainingMethod.LORA,
    )

    estimate = estimate_training_hardware(manifest)

    assert not estimate.fits_gpu_memory
    assert estimate.risk_level == "high"
    assert estimate.vram_margin_gb < 0


def test_training_hardware_estimate_handles_small_model_and_missing_gpu() -> None:
    small_manifest = build_draft_training_manifest(
        run_id="draft_small_001",
        base_model="small:1b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_small_001",
    )
    missing_gpu_manifest = small_manifest.model_copy(
        update={"hardware_profile": TrainingHardwareProfile(gpu_available=False)}
    )

    small_estimate = estimate_training_hardware(small_manifest)
    missing_gpu_report = build_training_dry_run_report(
        manifest=missing_gpu_manifest,
        examples=[
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
        ],
    )

    assert small_estimate.fits_gpu_memory
    assert small_estimate.risk_level == "low"
    assert missing_gpu_report.blocked_by_hardware
    assert "estimated_vram_exceeds_gpu" in missing_gpu_report.blocking_reasons
    assert any("GPU unavailable" in warning for warning in missing_gpu_report.warnings)


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
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# S.A.N.A. Training Dry Run" in markdown
    assert "## Hardware Estimate" in markdown
