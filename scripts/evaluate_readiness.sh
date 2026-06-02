#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIO_PATH="${1:-$ROOT_DIR/backend/tests/fixtures/v0_3_eval_scenarios.json}"
BASELINE_PATH="${2:-$ROOT_DIR/evaluation_reports/v0_5_baseline.json}"
REPORT_PATH="${3:-$ROOT_DIR/evaluation_reports/v0_5_latest.json}"
MARKDOWN_REPORT_PATH="${4:-$ROOT_DIR/evaluation_reports/v0_5_latest.md}"
REGRESSION_DIFF_PATH="${5:-$ROOT_DIR/evaluation_reports/v0_5_regression_diff.json}"
READINESS_PATH="${6:-$ROOT_DIR/evaluation_reports/v0_5_readiness.md}"
REVIEW_QUEUE_PATH="${7:-$ROOT_DIR/evaluation_reports/v0_5_expert_review_queue.json}"
REVIEW_MARKDOWN_PATH="${8:-$ROOT_DIR/evaluation_reports/v0_5_expert_review_queue.md}"
REVIEW_DECISIONS_PATH="${9:-}"
TRAINING_EXAMPLES_PATH="${10:-}"

if [ ! -f "$BASELINE_PATH" ]; then
  echo "Baseline not found; bootstrapping baseline: $BASELINE_PATH"
  "$ROOT_DIR/scripts/evaluate.sh" "$SCENARIO_PATH" "$BASELINE_PATH" >/tmp/sana-evaluate-baseline.log
fi

"$ROOT_DIR/scripts/evaluate.sh" \
  "$SCENARIO_PATH" \
  "$REPORT_PATH" \
  "$MARKDOWN_REPORT_PATH" \
  "$BASELINE_PATH" \
  "$REGRESSION_DIFF_PATH" \
  "$READINESS_PATH" \
  "$REVIEW_QUEUE_PATH" \
  "$REVIEW_MARKDOWN_PATH" \
  "$REVIEW_DECISIONS_PATH" \
  "$TRAINING_EXAMPLES_PATH" >/tmp/sana-evaluate-readiness.log

echo "Evaluation report: $REPORT_PATH"
echo "Markdown report: $MARKDOWN_REPORT_PATH"
echo "Regression diff: $REGRESSION_DIFF_PATH"
echo "Readiness decision: $READINESS_PATH"
echo "Expert review queue: $REVIEW_QUEUE_PATH"
echo "Expert review markdown: $REVIEW_MARKDOWN_PATH"
if [ -n "$REVIEW_DECISIONS_PATH" ]; then
  echo "Expert review decisions: $REVIEW_DECISIONS_PATH"
fi
if [ -n "$TRAINING_EXAMPLES_PATH" ]; then
  echo "Instruction training examples: $TRAINING_EXAMPLES_PATH"
fi
