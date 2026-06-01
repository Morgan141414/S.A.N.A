#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIO_PATH="${1:-$ROOT_DIR/backend/tests/fixtures/v0_3_eval_scenarios.json}"
REPORT_PATH="${2:-$ROOT_DIR/evaluation_reports/v0_4_latest.json}"
MARKDOWN_REPORT_PATH="${3:-$ROOT_DIR/evaluation_reports/v0_4_latest.md}"

"$ROOT_DIR/scripts/evaluate.sh" "$SCENARIO_PATH" "$REPORT_PATH" "$MARKDOWN_REPORT_PATH" >/tmp/sana-evaluate-report.log
echo "Evaluation report: $REPORT_PATH"
echo "Markdown report: $MARKDOWN_REPORT_PATH"
