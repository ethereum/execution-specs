#!/bin/bash
# Fill introduced test sources
# Usage: fill_introduced_tests.sh <changed_test_files> <patch_test_path>
# Exit codes:
#   0 - Success
#   1 - Failure to generate tests or no tests found

set -e

CHANGED_TEST_FILES="$1"
PATCH_TEST_PATH="$2"
BLOCK_GAS_LIMIT="${3:-45000000}"
FILL_UNTIL="${4:-Cancun}"

# Include basic evm operations into coverage by default
# As when we translate from yul/solidity some dup/push opcodes could become untouched
files="$CHANGED_TEST_FILES tests/homestead/coverage/test_coverage.py"

uv run fill $files --clean --until=$FILL_UNTIL --evm-bin evmone-t8n --block-gas-limit $BLOCK_GAS_LIMIT -m "state_test or blockchain_test" --output $PATCH_TEST_PATH > >(tee -a filloutput.log) 2> >(tee -a filloutput.log >&2)

if grep -q "FAILURES" filloutput.log; then
    echo "Error: failed to generate .py tests."
    exit 1
fi

exit 0