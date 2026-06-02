#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
SCENARIO_PATH="${1:-$BACKEND_DIR/tests/fixtures/v0_3_eval_scenarios.json}"
REPORT_PATH="${2:-}"
MARKDOWN_REPORT_PATH="${3:-}"
BASELINE_PATH="${4:-}"
REGRESSION_DIFF_PATH="${5:-}"
READINESS_PATH="${6:-}"
REVIEW_QUEUE_PATH="${7:-}"
REVIEW_MARKDOWN_PATH="${8:-}"
REVIEW_DECISIONS_PATH="${9:-}"
TRAINING_EXAMPLES_PATH="${10:-}"

resolve_optional_path() {
  local input_path="$1"
  if [ -z "$input_path" ] || [[ "$input_path" = /* ]]; then
    printf "%s" "$input_path"
  else
    printf "%s/%s" "$ROOT_DIR" "$input_path"
  fi
}

SCENARIO_PATH="$(resolve_optional_path "$SCENARIO_PATH")"
REPORT_PATH="$(resolve_optional_path "$REPORT_PATH")"
MARKDOWN_REPORT_PATH="$(resolve_optional_path "$MARKDOWN_REPORT_PATH")"
BASELINE_PATH="$(resolve_optional_path "$BASELINE_PATH")"
REGRESSION_DIFF_PATH="$(resolve_optional_path "$REGRESSION_DIFF_PATH")"
READINESS_PATH="$(resolve_optional_path "$READINESS_PATH")"
REVIEW_QUEUE_PATH="$(resolve_optional_path "$REVIEW_QUEUE_PATH")"
REVIEW_MARKDOWN_PATH="$(resolve_optional_path "$REVIEW_MARKDOWN_PATH")"
REVIEW_DECISIONS_PATH="$(resolve_optional_path "$REVIEW_DECISIONS_PATH")"
TRAINING_EXAMPLES_PATH="$(resolve_optional_path "$TRAINING_EXAMPLES_PATH")"

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

python -m pip install -e ".[dev]" >/tmp/sana-evaluate-install.log
if [ -n "$BASELINE_PATH" ] && [ -n "$REGRESSION_DIFF_PATH" ] && [ -n "$READINESS_PATH" ]; then
  python -m app.services.evaluation \
    "$SCENARIO_PATH" \
    "$REPORT_PATH" \
    "$MARKDOWN_REPORT_PATH" \
    "$BASELINE_PATH" \
    "$REGRESSION_DIFF_PATH" \
    "$READINESS_PATH" \
    "$REVIEW_QUEUE_PATH" \
    "$REVIEW_MARKDOWN_PATH" \
    "$REVIEW_DECISIONS_PATH" \
    "$TRAINING_EXAMPLES_PATH"
elif [ -n "$REPORT_PATH" ] && [ -n "$MARKDOWN_REPORT_PATH" ]; then
  python -m app.services.evaluation \
    "$SCENARIO_PATH" \
    "$REPORT_PATH" \
    "$MARKDOWN_REPORT_PATH" \
    "" \
    "" \
    "" \
    "$REVIEW_QUEUE_PATH" \
    "$REVIEW_MARKDOWN_PATH" \
    "$REVIEW_DECISIONS_PATH" \
    "$TRAINING_EXAMPLES_PATH"
elif [ -n "$REPORT_PATH" ]; then
  python -m app.services.evaluation "$SCENARIO_PATH" "$REPORT_PATH"
else
  python -m app.services.evaluation "$SCENARIO_PATH"
fi
