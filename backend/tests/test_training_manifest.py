from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.training_manifest import (
    TrainingGate,
    TrainingMethod,
    TrainingRunManifest,
    TrainingRunStatus,
    build_draft_training_manifest,
    load_training_manifest,
    write_training_manifest,
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
