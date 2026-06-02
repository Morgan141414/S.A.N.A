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
    build_training_dry_run_report,
    load_instruction_training_examples,
    load_training_manifest,
    write_training_dry_run_markdown,
    write_training_dry_run_report,
)

manifest = load_training_manifest(Path("$MANIFEST_PATH"))
examples = load_instruction_training_examples(Path("$DATASET_PATH"))
report = build_training_dry_run_report(manifest=manifest, examples=examples)
write_training_dry_run_report(report, Path("$REPORT_PATH"))
write_training_dry_run_markdown(report, Path("$MARKDOWN_REPORT_PATH"))
print(report.model_dump_json(indent=2))
PY

echo "Training dry-run report: $REPORT_PATH"
echo "Training dry-run markdown: $MARKDOWN_REPORT_PATH"
