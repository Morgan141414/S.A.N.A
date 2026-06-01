#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "== S.A.N.A. development cycle =="
echo "1. Running quality gate"
"$ROOT_DIR/scripts/check.sh"

echo
echo "2. Generating quality report"
"$ROOT_DIR/scripts/quality_report.sh" > "$ROOT_DIR/quality_report.md"

echo
echo "3. Development cycle completed"
echo "Report: $ROOT_DIR/quality_report.md"

