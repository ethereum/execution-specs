#!/usr/bin/env bash
set -euo pipefail

STATIC_OUTPUT="output/compiled_static"
PYTHON_OUTPUT="output/fixtures_python"
PORTED_DIR="tests/ported_static"
PARALLEL="${1:-10}"

echo "=== Step 1: Fill static tests ==="
TMPDIR=./.tmp uv run fill --fill-static-tests \
    --output "$STATIC_OUTPUT" --clean -n "$PARALLEL" tests/static/

echo ""
echo "=== Step 2: Generate ported tests ==="
uv run python scripts/fixture_to_python.py \
    --fixtures "$STATIC_OUTPUT/state_tests/" \
    --fillers tests/static/state_tests/ \
    --output "$PORTED_DIR"

echo ""
echo "=== Step 3: Fill ported tests ==="
TMPDIR=./.tmp uv run fill "$PORTED_DIR" \
    --output "$PYTHON_OUTPUT" --clean -n "$PARALLEL"

echo ""
echo "=== Step 4: Compare fixtures ==="
uv run python scripts/compare_fixtures.py \
    "$STATIC_OUTPUT" "$PYTHON_OUTPUT"

echo ""
echo "=== Step 5: Lint ==="
uvx tox -e static
