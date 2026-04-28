#!/bin/bash
# Verify that filler_to_python with dynamic addresses produces
# trace-equivalent tests. Assumes output/traces_baseline/ already
# exists (generated once before any code changes).
set -euo pipefail

export TMPDIR=./.tmp
mkdir -p "$TMPDIR" output/traces_new

if [ ! -d "output/traces_baseline" ]; then
    echo "ERROR: output/traces_baseline/ not found."
    echo "Generate baseline first (before code changes):"
    echo "  TMPDIR=./.tmp uv run fill tests/ported_static/ --evm-dump-dir output/traces_baseline -n 10 -m 'not slow'"
    exit 1
fi

# Step 1: Run filler_to_python (overwrites tests/ported_static/)
echo "=== Step 1: Running filler_to_python ==="
uv run python -m scripts.filler_to_python \
    --fillers tests/static/static/state_tests/ \
    --output tests/ported_static/

# Step 2: Fill new tests + verify against baseline
echo "=== Step 2: Filling new tests and verifying traces ==="
uv run fill \
    tests/ported_static/ \
    --evm-dump-dir output/traces_new \
    --verify-traces output/traces_baseline \
    --verify-traces-comparator exact-no-stack \
    -n 10 \
    -m "not slow"

echo "=== Done. Check output above for trace mismatches ==="
echo "=== Use 'git diff tests/ported_static/' to see code changes ==="
