from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.training_manifest import (
    TrainingGate,
    TrainingHardwareProfile,
    TrainingMethod,
    TrainingRunManifest,
    TrainingRunStatus,
    build_training_dataset_manifest,
    build_training_profiler_evidence,
    build_training_dry_run_report,
    build_draft_training_manifest,
    estimate_training_hardware,
    load_training_manifest,
    parse_nvidia_smi_evidence,
    write_training_dry_run_markdown,
    write_training_dry_run_report,
    write_training_manifest,
)
from app.services.evaluation import InstructionTrainingExample, ReviewDecision, ScenarioSourceType
from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskLevel
from app.services.support_protocols import SupportProtocol


def _safe_example(
    example_id: str,
    *,
    risk_level: RiskLevel = RiskLevel.LOW,
    conversation_mode: ConversationMode = ConversationMode.SUPPORT,
    support_protocol: SupportProtocol = SupportProtocol.GENERAL_SUPPORT,
    reviewer_decision: ReviewDecision = ReviewDecision.APPROVED,
) -> InstructionTrainingExample:
    return InstructionTrainingExample(
        id=example_id,
        dataset_version="v0.4.0",
        source_type=ScenarioSourceType.CLINICIAN_AUTHORED,
        locale="ru",
        user_message=f"Мне тревожно, case {example_id}",
        assistant_response="Я рядом. Давай начнем с одного спокойного шага.",
        risk_level=risk_level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        reviewer_decision=reviewer_decision,
    )


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
    assert "minor_support" in manifest.forbidden_conversation_modes
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
        _safe_example("safe_review_case")
    ]

    report = build_training_dry_run_report(manifest=manifest, examples=examples)

    assert report.blocked
    assert report.dataset_total == 1
    assert report.train_examples == 1
    assert report.validation_examples == 0
    assert report.estimated_optimizer_steps == 1
    assert report.dataset_manifest.total_examples == 1
    assert report.dataset_manifest.train_example_ids == ["safe_review_case"]
    assert report.dataset_manifest.validation_example_ids == []
    assert len(report.dataset_manifest.dataset_fingerprint) == 64
    assert len(report.dataset_manifest.train_ids_fingerprint) == 64
    assert report.hardware_estimate.risk_level in {"low", "medium"}
    assert report.profiler_evidence.source == "not_collected"
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


def test_training_dry_run_blocks_duplicate_training_example_ids() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )

    report = build_training_dry_run_report(
        manifest=manifest,
        examples=[_safe_example("duplicate_case"), _safe_example("duplicate_case")],
    )

    assert report.blocked_by_dataset_safety
    assert "duplicate_training_example_id:duplicate_case" in report.blocking_reasons
    assert report.dataset_manifest.total_examples == 2


def test_training_dry_run_blocks_unapproved_or_minor_training_examples() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )

    report = build_training_dry_run_report(
        manifest=manifest,
        examples=[
            _safe_example("pending_case", reviewer_decision=ReviewDecision.PENDING),
            _safe_example(
                "minor_case",
                conversation_mode=ConversationMode.MINOR_SUPPORT,
                support_protocol=SupportProtocol.MINOR_SUPPORT,
            ),
        ],
    )

    assert report.blocked_by_dataset_safety
    assert "forbidden_reviewer_decision:pending_case:pending" in report.blocking_reasons
    assert "forbidden_conversation_mode:minor_case:minor_support" in report.blocking_reasons


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
            _safe_example("safe_review_case")
        ],
    )

    assert small_estimate.fits_gpu_memory
    assert small_estimate.risk_level == "low"
    assert missing_gpu_report.blocked_by_hardware
    assert "estimated_vram_exceeds_gpu" in missing_gpu_report.blocking_reasons
    assert any("GPU unavailable" in warning for warning in missing_gpu_report.warnings)


def test_training_dataset_manifest_is_reproducible_and_order_independent() -> None:
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path="evaluation_reports/approved_instruction_examples.json",
        output_dir="training_runs/draft_qlora_001",
    )
    examples = [
        _safe_example("case_003", risk_level=RiskLevel.MEDIUM),
        _safe_example("case_001"),
        _safe_example("case_002", support_protocol=SupportProtocol.ANXIETY_GROUNDING),
    ]

    first = build_training_dataset_manifest(manifest=manifest, examples=examples)
    second = build_training_dataset_manifest(manifest=manifest, examples=list(reversed(examples)))

    assert first.dataset_fingerprint == second.dataset_fingerprint
    assert first.example_ids_fingerprint == second.example_ids_fingerprint
    assert first.train_example_ids == second.train_example_ids
    assert first.validation_example_ids == second.validation_example_ids
    assert first.train_ids_fingerprint == second.train_ids_fingerprint
    assert first.validation_ids_fingerprint == second.validation_ids_fingerprint
    assert first.split_algorithm == "sha256_sorted_id"
    assert first.total_examples == 3
    assert len(first.validation_example_ids) == 1
    assert sorted(first.train_example_ids + first.validation_example_ids) == [
        "case_001",
        "case_002",
        "case_003",
    ]
    assert first.risk_level_counts == {"low": 2, "medium": 1}
    assert first.support_protocol_counts["anxiety_grounding"] == 1


def test_training_profiler_evidence_defaults_to_not_collected() -> None:
    evidence = build_training_profiler_evidence(collect=False)

    assert evidence.source == "not_collected"
    assert evidence.gpu_detected is None
    assert any("not collected" in note for note in evidence.notes)


def test_training_profiler_evidence_parses_nvidia_smi_csv() -> None:
    evidence = parse_nvidia_smi_evidence(
        "NVIDIA GeForce RTX 3050, 8192, 4096, 550.54.14\n"
    )

    assert evidence.source == "nvidia_smi"
    assert evidence.gpu_detected is True
    assert evidence.gpu_name == "NVIDIA GeForce RTX 3050"
    assert evidence.gpu_vram_total_gb == 8.0
    assert evidence.gpu_vram_free_gb == 4.0
    assert evidence.driver_version == "550.54.14"


def test_training_profiler_evidence_handles_malformed_nvidia_smi_csv() -> None:
    evidence = parse_nvidia_smi_evidence("unexpected output\n")

    assert evidence.source == "nvidia_smi_malformed"
    assert evidence.gpu_detected is None
    assert any("expected CSV" in note for note in evidence.notes)


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
    assert "## Dataset Manifest" in markdown
    assert "## Profiler Evidence" in markdown
    assert '"profiler_evidence"' in json_path.read_text(encoding="utf-8")
    assert '"dataset_manifest"' in json_path.read_text(encoding="utf-8")
