#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
MANIFEST_PATH="${1:-$ROOT_DIR/training_runs/draft_training_manifest.json}"
DATASET_PATH="${2:-$ROOT_DIR/evaluation_reports/approved_instruction_examples.json}"
REPORT_PATH="${3:-$ROOT_DIR/training_runs/dry_run_report.json}"
MARKDOWN_REPORT_PATH="${4:-$ROOT_DIR/training_runs/dry_run_report.md}"

resolve_optional_path() {
  local input_path="$1"
  if [ -z "$input_path" ] || [[ "$input_path" = /* ]]; then
    printf "%s" "$input_path"
  else
    printf "%s/%s" "$ROOT_DIR" "$input_path"
  fi
}

MANIFEST_PATH="$(resolve_optional_path "$MANIFEST_PATH")"
DATASET_PATH="$(resolve_optional_path "$DATASET_PATH")"
REPORT_PATH="$(resolve_optional_path "$REPORT_PATH")"
MARKDOWN_REPORT_PATH="$(resolve_optional_path "$MARKDOWN_REPORT_PATH")"

cd "$BACKEND_DIR"

if [ -d ".venv" ] && [ ! -f ".venv/bin/activate" ]; then
  echo "backend/.venv exists but is incomplete; recreating it." >&2
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  if ! python3 -m venv .venv; then
    echo "Could not create backend/.venv. Install python3-venv or create the venv manually." >&2
    exit 1
  fi
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -e ".[dev]" >/tmp/sana-training-dry-run-install.log
python - <<PY
from pathlib import Path

from app.services.training_manifest import (
    build_training_profiler_evidence,
    build_training_dry_run_report,
    build_draft_training_manifest,
    load_instruction_training_examples,
    load_training_manifest,
    write_training_dry_run_markdown,
    write_training_dry_run_report,
    write_training_manifest,
)

manifest_path = Path("$MANIFEST_PATH")
dataset_path = Path("$DATASET_PATH")
if not manifest_path.exists():
    manifest = build_draft_training_manifest(
        run_id="draft_qlora_001",
        base_model="llama3.1:8b",
        dataset_path=str(dataset_path),
        output_dir=str(Path("$REPORT_PATH").parent),
    )
    write_training_manifest(manifest, manifest_path)
else:
    manifest = load_training_manifest(manifest_path)

examples = load_instruction_training_examples(dataset_path) if dataset_path.exists() else []
collect_profiler = "${SANA_TRAINING_COLLECT_PROFILER:-}".lower() in {"1", "true", "yes"}
profiler_evidence = build_training_profiler_evidence(collect=collect_profiler)
report = build_training_dry_run_report(
    manifest=manifest,
    examples=examples,
    profiler_evidence=profiler_evidence,
)
write_training_dry_run_report(report, Path("$REPORT_PATH"))
write_training_dry_run_markdown(report, Path("$MARKDOWN_REPORT_PATH"))
print(report.model_dump_json(indent=2))
PY

echo "Training dry-run report: $REPORT_PATH"
echo "Training dry-run markdown: $MARKDOWN_REPORT_PATH"
