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
    "$READINESS_PATH"
elif [ -n "$REPORT_PATH" ] && [ -n "$MARKDOWN_REPORT_PATH" ]; then
  python -m app.services.evaluation "$SCENARIO_PATH" "$REPORT_PATH" "$MARKDOWN_REPORT_PATH"
elif [ -n "$REPORT_PATH" ]; then
  python -m app.services.evaluation "$SCENARIO_PATH" "$REPORT_PATH"
else
  python -m app.services.evaluation "$SCENARIO_PATH"
fi
