from pathlib import Path
import json
import math
import re
import shutil
import subprocess

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


class TrainingAdapterConfig(BaseModel):
    adapter_rank: int = Field(default=16, ge=1, le=256)
    adapter_alpha: int = Field(default=32, ge=1, le=512)
    target_modules: list[str] = Field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    quantization_bits: int = Field(default=4, ge=4, le=16)
    optimizer: str = "paged_adamw_8bit"
    gradient_checkpointing: bool = True
    compute_dtype: str = "float16"


class TrainingHardwareProfile(BaseModel):
    gpu_available: bool = True
    gpu_vram_gb: float = Field(default=8.0, gt=0, le=256)
    system_ram_gb: float = Field(default=31.0, gt=0, le=1024)
    gpu_name: str = "RTX 3050"
    notes: str = "Estimate only; verify with real training profiler before fine-tuning."


class TrainingHardwareEstimate(BaseModel):
    gpu_name: str
    gpu_available: bool
    estimated_vram_gb: float
    estimated_system_ram_gb: float
    vram_margin_gb: float
    system_ram_margin_gb: float
    fits_gpu_memory: bool
    fits_system_memory: bool
    risk_level: str
    confidence: str
    notes: list[str] = Field(default_factory=list)


class TrainingProfilerEvidence(BaseModel):
    source: str = "not_collected"
    gpu_detected: bool | None = None
    gpu_name: str | None = None
    gpu_vram_total_gb: float | None = None
    gpu_vram_free_gb: float | None = None
    system_ram_total_gb: float | None = None
    cuda_available: bool | None = None
    driver_version: str | None = None
    collection_command: str | None = None
    notes: list[str] = Field(default_factory=list)


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
    adapter_config: TrainingAdapterConfig = Field(default_factory=TrainingAdapterConfig)
    hardware_profile: TrainingHardwareProfile = Field(default_factory=TrainingHardwareProfile)
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
    hardware_estimate: TrainingHardwareEstimate
    profiler_evidence: TrainingProfilerEvidence
    blocked_by_readiness: bool
    blocked_by_dataset_safety: bool
    blocked_by_hardware: bool
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
    profiler_evidence: TrainingProfilerEvidence | None = None,
) -> TrainingDryRunReport:
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    blocked_by_readiness = False
    blocked_by_dataset_safety = False
    blocked_by_hardware = False
    if manifest.status == TrainingRunStatus.BLOCKED_UNTIL_READINESS:
        blocked_by_readiness = True
        blocking_reasons.append("manifest_blocked_until_readiness")
    if not examples:
        blocked_by_dataset_safety = True
        blocking_reasons.append("dataset_empty")

    for example in examples:
        if example.risk_level.value not in manifest.allowed_risk_levels:
            blocked_by_dataset_safety = True
            blocking_reasons.append(f"forbidden_risk_level:{example.id}:{example.risk_level.value}")
        if example.conversation_mode.value in manifest.forbidden_conversation_modes:
            blocked_by_dataset_safety = True
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
    hardware_estimate = estimate_training_hardware(manifest)
    profiler_evidence = profiler_evidence or build_training_profiler_evidence(collect=False)
    if not hardware_estimate.fits_gpu_memory:
        blocked_by_hardware = True
        blocking_reasons.append("estimated_vram_exceeds_gpu")
    if not hardware_estimate.fits_system_memory:
        blocked_by_hardware = True
        blocking_reasons.append("estimated_ram_exceeds_system")
    warnings.extend(hardware_estimate.notes)

    return TrainingDryRunReport(
        run_id=manifest.run_id,
        status=manifest.status,
        blocked=bool(blocking_reasons),
        dataset_total=len(examples),
        train_examples=train_examples,
        validation_examples=validation_examples,
        estimated_optimizer_steps=estimated_optimizer_steps,
        hardware_estimate=hardware_estimate,
        profiler_evidence=profiler_evidence,
        blocked_by_readiness=blocked_by_readiness,
        blocked_by_dataset_safety=blocked_by_dataset_safety,
        blocked_by_hardware=blocked_by_hardware,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )


def build_training_profiler_evidence(*, collect: bool = False) -> TrainingProfilerEvidence:
    if not collect:
        return TrainingProfilerEvidence(
            notes=["Profiler evidence was not collected; hardware section is heuristic only."]
        )

    command = shutil.which("nvidia-smi")
    if not command:
        return TrainingProfilerEvidence(
            source="nvidia_smi_unavailable",
            gpu_detected=False,
            collection_command="nvidia-smi",
            notes=["nvidia-smi is unavailable; cannot collect GPU profiler evidence."],
        )

    try:
        result = subprocess.run(
            [
                command,
                "--query-gpu=name,memory.total,memory.free,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return TrainingProfilerEvidence(
            source="nvidia_smi_error",
            gpu_detected=False,
            collection_command="nvidia-smi",
            notes=[f"nvidia-smi profiler collection failed: {exc.__class__.__name__}"],
        )

    if result.returncode != 0:
        return TrainingProfilerEvidence(
            source="nvidia_smi_error",
            gpu_detected=False,
            collection_command="nvidia-smi",
            notes=["nvidia-smi returned a non-zero exit code."],
        )

    return parse_nvidia_smi_evidence(result.stdout)


def parse_nvidia_smi_evidence(output: str) -> TrainingProfilerEvidence:
    line = next((candidate.strip() for candidate in output.splitlines() if candidate.strip()), "")
    if not line:
        return TrainingProfilerEvidence(
            source="nvidia_smi_empty",
            gpu_detected=False,
            collection_command="nvidia-smi",
            notes=["nvidia-smi returned no GPU rows."],
        )

    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 4:
        return TrainingProfilerEvidence(
            source="nvidia_smi_malformed",
            gpu_detected=None,
            collection_command="nvidia-smi",
            notes=["nvidia-smi output did not match expected CSV shape."],
        )

    total_mb = _parse_float(parts[1])
    free_mb = _parse_float(parts[2])
    return TrainingProfilerEvidence(
        source="nvidia_smi",
        gpu_detected=True,
        gpu_name=parts[0],
        gpu_vram_total_gb=round(total_mb / 1024, 2) if total_mb is not None else None,
        gpu_vram_free_gb=round(free_mb / 1024, 2) if free_mb is not None else None,
        driver_version=parts[3],
        collection_command="nvidia-smi",
        notes=["Profiler evidence collected from nvidia-smi; still verify with a real training run profiler."],
    )


def estimate_training_hardware(manifest: TrainingRunManifest) -> TrainingHardwareEstimate:
    model_b = _infer_model_billions(manifest.base_model)
    if manifest.method == TrainingMethod.QLORA:
        quant_multiplier = manifest.adapter_config.quantization_bits / 4
        estimated_vram_gb = (0.8 * model_b + 1.2) * quant_multiplier
        method_note = "QLoRA estimate assumes 4-bit base weights plus adapter/optimizer overhead."
    else:
        estimated_vram_gb = 2.4 * model_b + 4.0
        method_note = "LoRA estimate is conservative for non-quantized fine-tuning."

    adapter_multiplier = max(1.0, manifest.adapter_config.adapter_rank / 16)
    sequence_multiplier = manifest.hyperparameters.max_seq_length / 2048
    batch_multiplier = max(1.0, manifest.hyperparameters.batch_size / 1)
    estimated_vram_gb *= max(1.0, sequence_multiplier) * batch_multiplier * adapter_multiplier
    if manifest.adapter_config.gradient_checkpointing:
        estimated_vram_gb *= 0.9
    estimated_system_ram_gb = max(8.0, 1.8 * model_b + 6.0)

    notes = [method_note]
    if not manifest.hardware_profile.gpu_available:
        notes.append("GPU unavailable or not detected; dry-run cannot confirm GPU fit.")
    if manifest.hardware_profile.gpu_vram_gb <= 8 and estimated_vram_gb > 0:
        notes.append("8GB VRAM is a tight target; expect small batch size and careful monitoring.")
    if manifest.hyperparameters.max_seq_length > 2048:
        notes.append("Long context increases activation memory.")
    if manifest.adapter_config.adapter_rank > 16:
        notes.append("Higher adapter rank increases adapter and optimizer memory.")

    fits_gpu_memory = (
        manifest.hardware_profile.gpu_available
        and estimated_vram_gb <= manifest.hardware_profile.gpu_vram_gb
    )
    fits_system_memory = estimated_system_ram_gb <= manifest.hardware_profile.system_ram_gb
    vram_margin_gb = manifest.hardware_profile.gpu_vram_gb - estimated_vram_gb
    system_ram_margin_gb = manifest.hardware_profile.system_ram_gb - estimated_system_ram_gb
    if not fits_gpu_memory or not fits_system_memory:
        risk_level = "high"
    elif estimated_vram_gb >= manifest.hardware_profile.gpu_vram_gb * 0.85:
        risk_level = "medium"
        notes.append("Estimated VRAM is close to the GPU limit.")
    else:
        risk_level = "low"
    confidence = "low" if model_b == 8.0 and "8b" not in manifest.base_model.lower() else "medium"

    return TrainingHardwareEstimate(
        gpu_name=manifest.hardware_profile.gpu_name,
        gpu_available=manifest.hardware_profile.gpu_available,
        estimated_vram_gb=round(estimated_vram_gb, 2),
        estimated_system_ram_gb=round(estimated_system_ram_gb, 2),
        vram_margin_gb=round(vram_margin_gb, 2),
        system_ram_margin_gb=round(system_ram_margin_gb, 2),
        fits_gpu_memory=fits_gpu_memory,
        fits_system_memory=fits_system_memory,
        risk_level=risk_level,
        confidence=confidence,
        notes=notes,
    )


def _infer_model_billions(model_name: str) -> float:
    lowered = model_name.lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*b", lowered)
    if match:
        return float(match.group(1))
    if "8b" in lowered:
        return 8.0
    if "7b" in lowered:
        return 7.0
    if "9b" in lowered:
        return 9.0
    return 8.0


def _parse_float(raw_value: str) -> float | None:
    try:
        return float(raw_value.strip())
    except ValueError:
        return None


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
        f"- Blocked by readiness: {str(report.blocked_by_readiness).lower()}",
        f"- Blocked by dataset safety: {str(report.blocked_by_dataset_safety).lower()}",
        f"- Blocked by hardware: {str(report.blocked_by_hardware).lower()}",
        "",
        "## Hardware Estimate",
        "",
        f"- GPU: `{report.hardware_estimate.gpu_name}`",
        f"- GPU available: {str(report.hardware_estimate.gpu_available).lower()}",
        f"- Estimated VRAM GB: {report.hardware_estimate.estimated_vram_gb}",
        f"- VRAM margin GB: {report.hardware_estimate.vram_margin_gb}",
        f"- Estimated system RAM GB: {report.hardware_estimate.estimated_system_ram_gb}",
        f"- System RAM margin GB: {report.hardware_estimate.system_ram_margin_gb}",
        f"- Fits GPU memory: {str(report.hardware_estimate.fits_gpu_memory).lower()}",
        f"- Fits system memory: {str(report.hardware_estimate.fits_system_memory).lower()}",
        f"- Hardware risk: `{report.hardware_estimate.risk_level}`",
        f"- Estimate confidence: `{report.hardware_estimate.confidence}`",
        "",
        "## Profiler Evidence",
        "",
        f"- Source: `{report.profiler_evidence.source}`",
        f"- GPU detected: {report.profiler_evidence.gpu_detected}",
        f"- GPU: `{report.profiler_evidence.gpu_name}`",
        f"- Total VRAM GB: {report.profiler_evidence.gpu_vram_total_gb}",
        f"- Free VRAM GB: {report.profiler_evidence.gpu_vram_free_gb}",
        f"- CUDA available: {report.profiler_evidence.cuda_available}",
        f"- Driver version: `{report.profiler_evidence.driver_version}`",
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
