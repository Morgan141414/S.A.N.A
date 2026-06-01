#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
REPORT_PATH="${1:-$ROOT_DIR/evaluation_reports/v0_8_provider_smoke.json}"
MARKDOWN_REPORT_PATH="${2:-$ROOT_DIR/evaluation_reports/v0_8_provider_smoke.md}"

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

python -m pip install -e ".[dev]" >/tmp/sana-llm-smoke-install.log
python -m app.services.llm_smoke "$REPORT_PATH" "$MARKDOWN_REPORT_PATH"
