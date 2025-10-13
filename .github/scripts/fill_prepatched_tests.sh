#!/bin/bash
# Fill pre-patched test sources from before the PR
# Usage: fill_prepatched_tests.sh <modified_deleted_test_files> <base_test_path> <patch_test_path> <block_gas_limit> <fill_until>
# Exit codes:
#   0 - Success
#   1 - Failure to generate tests

set -e

MODIFIED_DELETED_FILES="$1"
BASE_TEST_PATH="$2"
PATCH_TEST_PATH="$3"
BLOCK_GAS_LIMIT="${4:-45000000}"
FILL_UNTIL="${5:-Cancun}"

echo "--------------------"
echo "converted-ethereum-tests.txt seem untouched, try to fill pre-patched version of .py files:"

PATCH_COMMIT=$(git rev-parse HEAD)
git checkout main
BASE_COMMIT=$(git rev-parse HEAD)
echo "Checkout head $BASE_COMMIT"

echo "Select files that were changed and exist on the main branch:"
echo "$MODIFIED_DELETED_FILES"

rm -rf fixtures

set +e
uv run fill $MODIFIED_DELETED_FILES --clean --until=$FILL_UNTIL --evm-bin evmone-t8n --block-gas-limit $BLOCK_GAS_LIMIT -m "state_test or blockchain_test" --output $BASE_TEST_PATH
FILL_RETURN_CODE=$?
set -e
if [ $FILL_RETURN_CODE -eq 5 ]; then
    echo "any_modified_fixtures=false" >> "$GITHUB_OUTPUT"
    exit 0
elif [ $FILL_RETURN_CODE -ne 0 ]; then
    echo "Error: failed to generate .py tests from before the PR."
    exit 1
fi

git checkout $PATCH_COMMIT
echo "Checkout back to patch $PATCH_COMMIT"
# abort-on-empty-patch is used to ensure that the patch folder is not empty after fixture removal.
# If the patch folder would be empty, it means that fixtures were removed in the PR, in which case we still want to run the coverage check.
uv run compare_fixtures --abort-on-empty-patch $BASE_TEST_PATH $PATCH_TEST_PATH

if [ -d $BASE_TEST_PATH ]; then
    # If the base folder is not empty, it means there's at least one fixture that was modified in the PR, continue with the coverage check.
    echo "Base folder is not empty after fixture comparison, continuing with coverage check."
    echo "any_modified_fixtures=true" >> "$GITHUB_OUTPUT"
else
    # If the base folder is empty, it means there were no fixtures that were modified in the PR, or fixtures were only added, so we can skip the coverage check.
    echo "Base folder is empty after fixture comparison, skipping coverage check."
    echo "any_modified_fixtures=false" >> "$GITHUB_OUTPUT"
fi
exit 0