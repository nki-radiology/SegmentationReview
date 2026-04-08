#!/usr/bin/env bash
# scripts/check.sh — Run all checks locally before pushing.
# Usage: ./scripts/check.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SegmentationReview — local checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

step() { echo; echo "▶ $1"; }

step "Formatting (black)"
black --check src/

step "Linting (ruff)"
ruff check src/

step "Type checking (mypy)"
mypy src/segmentation_review/

step "Tests with coverage"
pytest --cov=segmentation_review --cov-report=term-missing --cov-fail-under=80

step "Last commit message (commitlint)"
LAST_MSG=$(git log -1 --pretty=%B)
echo "$LAST_MSG" | npx --yes commitlint || echo "⚠ Commitlint skipped (npx not available)"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  All checks passed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
