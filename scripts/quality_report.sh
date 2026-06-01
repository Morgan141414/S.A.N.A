#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "# S.A.N.A. Quality Report"
echo
echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "## Git"
  echo
  echo "- Branch: $(git branch --show-current)"
  echo "- Commit: $(git rev-parse --short HEAD)"
  echo
  echo "### Working Tree"
  echo
  git status --short || true
  echo
fi

echo "## Checks"
echo
if "$ROOT_DIR/scripts/check.sh" >/tmp/sana-quality-check.log 2>&1; then
  echo "- Quality gate: passed"
else
  echo "- Quality gate: failed"
  echo
  echo '```text'
  tail -120 /tmp/sana-quality-check.log
  echo '```'
  exit 1
fi

echo
echo "## Test Summary"
echo
grep -E "passed|failed|error|warnings" /tmp/sana-quality-check.log | tail -20 || true

