from pathlib import Path
import json
import math

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.services.evaluation import InstructionTrainingExample


class TrainingMethod(StrEnum):
    LORA = "lora"
    QLORA = "qlora"


class TrainingRunStatus(StrEnum):
    DRAFT = "draft"
    BLOCKED_UNTIL_READINESS = "blocked_until_readiness"
    READY_FOR_DRY_RUN = "ready_for_dry_run"
    READY_FOR_TRAINING = "ready_for_training"


class TrainingHyperparameters(BaseModel):
    epochs: int = Field(default=1, ge=1, le=5)
    learning_rate: float = Field(default=0.00002, gt=0, le=0.001)
    batch_size: int = Field(default=1, ge=1, le=16)
    gradient_accumulation_steps: int = Field(default=16, ge=1, le=128)
    max_seq_length: int = Field(default=2048, ge=512, le=8192)
    validation_split: float = Field(default=0.1, ge=0.05, le=0.3)


class TrainingGate(StrEnum):
    APPROVED_LOW_MEDIUM_ONLY = "approved_low_medium_only"
    NO_CRISIS_EMERGENCY_MINOR = "no_crisis_emergency_minor"
    EVALUATION_BASELINE_GREEN = "evaluation_baseline_green"
    EXPERT_REVIEW_COMPLETE = "expert_review_complete"
    ROLLBACK_PLAN_DEFINED = "rollback_plan_defined"
    LOCAL_MODEL_BASELINE_RECORDED = "local_model_baseline_recorded"


class TrainingRunManifest(BaseModel):
    run_id: str
    base_model: str
    method: TrainingMethod
    dataset_path: str
    output_dir: str
    status: TrainingRunStatus
    hyperparameters: TrainingHyperparameters = Field(default_factory=TrainingHyperparameters)
    required_gates: list[TrainingGate] = Field(default_factory=list)
    allowed_risk_levels: list[str] = Field(default_factory=lambda: ["low", "medium"])
    forbidden_conversation_modes: list[str] = Field(
        default_factory=lambda: ["crisis", "emergency", "minor_safety"]
    )
    metrics_to_compare: list[str] = Field(
        default_factory=lambda: [
            "evaluation_pass_rate",
            "protocol_pass_rate",
            "llm_candidate_used_count",
            "llm_fallback_count",
            "language_artifact_count",
            "safety_failure_count",
        ]
    )
    notes: str = ""

    @model_validator(mode="after")
    def require_safety_gates(self) -> "TrainingRunManifest":
        required = {
            TrainingGate.APPROVED_LOW_MEDIUM_ONLY,
            TrainingGate.NO_CRISIS_EMERGENCY_MINOR,
            TrainingGate.EVALUATION_BASELINE_GREEN,
            TrainingGate.EXPERT_REVIEW_COMPLETE,
            TrainingGate.ROLLBACK_PLAN_DEFINED,
            TrainingGate.LOCAL_MODEL_BASELINE_RECORDED,
        }
        missing = required - set(self.required_gates)
        if missing:
            joined = ", ".join(sorted(gate.value for gate in missing))
            raise ValueError(f"training manifest missing required gates: {joined}")
        return self


class TrainingDryRunReport(BaseModel):
    run_id: str
    status: TrainingRunStatus
    blocked: bool
    dataset_total: int
    train_examples: int
    validation_examples: int
    estimated_optimizer_steps: int
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def build_draft_training_manifest(
    *,
    run_id: str,
    base_model: str,
    dataset_path: str,
    output_dir: str,
    method: TrainingMethod = TrainingMethod.QLORA,
) -> TrainingRunManifest:
    return TrainingRunManifest(
        run_id=run_id,
        base_model=base_model,
        method=method,
        dataset_path=dataset_path,
        output_dir=output_dir,
        status=TrainingRunStatus.BLOCKED_UNTIL_READINESS,
        required_gates=[
            TrainingGate.APPROVED_LOW_MEDIUM_ONLY,
            TrainingGate.NO_CRISIS_EMERGENCY_MINOR,
            TrainingGate.EVALUATION_BASELINE_GREEN,
            TrainingGate.EXPERT_REVIEW_COMPLETE,
            TrainingGate.ROLLBACK_PLAN_DEFINED,
            TrainingGate.LOCAL_MODEL_BASELINE_RECORDED,
        ],
        notes="Draft only. Do not start fine-tuning until all readiness gates are satisfied.",
    )


def write_training_manifest(manifest: TrainingRunManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_training_manifest(path: Path) -> TrainingRunManifest:
    return TrainingRunManifest.model_validate_json(path.read_text(encoding="utf-8"))


def load_instruction_training_examples(path: Path) -> list[InstructionTrainingExample]:
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    return [InstructionTrainingExample.model_validate(item) for item in raw_data]


def build_training_dry_run_report(
    *,
    manifest: TrainingRunManifest,
    examples: list[InstructionTrainingExample],
) -> TrainingDryRunReport:
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    if manifest.status == TrainingRunStatus.BLOCKED_UNTIL_READINESS:
        blocking_reasons.append("manifest_blocked_until_readiness")
    if not examples:
        blocking_reasons.append("dataset_empty")

    for example in examples:
        if example.risk_level.value not in manifest.allowed_risk_levels:
            blocking_reasons.append(f"forbidden_risk_level:{example.id}:{example.risk_level.value}")
        if example.conversation_mode.value in manifest.forbidden_conversation_modes:
            blocking_reasons.append(
                f"forbidden_conversation_mode:{example.id}:{example.conversation_mode.value}"
            )

    validation_examples = math.ceil(len(examples) * manifest.hyperparameters.validation_split)
    if len(examples) == 1:
        validation_examples = 0
        warnings.append("validation_split_disabled_for_single_example")
    elif len(examples) > 1:
        validation_examples = max(1, min(validation_examples, len(examples) - 1))
    train_examples = max(0, len(examples) - validation_examples)
    effective_batch_size = (
        manifest.hyperparameters.batch_size
        * manifest.hyperparameters.gradient_accumulation_steps
    )
    estimated_optimizer_steps = (
        math.ceil(train_examples / effective_batch_size) * manifest.hyperparameters.epochs
        if train_examples
        else 0
    )

    return TrainingDryRunReport(
        run_id=manifest.run_id,
        status=manifest.status,
        blocked=bool(blocking_reasons),
        dataset_total=len(examples),
        train_examples=train_examples,
        validation_examples=validation_examples,
        estimated_optimizer_steps=estimated_optimizer_steps,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )


def write_training_dry_run_report(report: TrainingDryRunReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_training_dry_run_markdown(report: TrainingDryRunReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# S.A.N.A. Training Dry Run",
        "",
        f"- Run id: `{report.run_id}`",
        f"- Status: `{report.status.value}`",
        f"- Blocked: {str(report.blocked).lower()}",
        f"- Dataset total: {report.dataset_total}",
        f"- Train examples: {report.train_examples}",
        f"- Validation examples: {report.validation_examples}",
        f"- Estimated optimizer steps: {report.estimated_optimizer_steps}",
        "",
        "## Blocking Reasons",
        "",
    ]
    if report.blocking_reasons:
        lines.extend(f"- `{reason}`" for reason in report.blocking_reasons)
    else:
        lines.append("No blocking reasons.")
    lines.extend(["", "## Warnings", ""])
    if report.warnings:
        lines.extend(f"- `{warning}`" for warning in report.warnings)
    else:
        lines.append("No warnings.")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
