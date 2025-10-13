#!/bin/bash
# Parse ported_from markers from introduced .py tests
# Usage: parse_ported_tests.sh <changed_test_files> <workspace_path>
# Exit codes:
#   0 - Found converted tests, continue processing
#   1 - No converted tests found, but updates detected

set -e

CHANGED_TEST_FILES="$1"
WORKSPACE_PATH="${2:-$GITHUB_WORKSPACE}"

echo "Changed or new test files: $CHANGED_TEST_FILES"

FILTERED_FILES=""
for file in $CHANGED_TEST_FILES; do
    if git diff origin/main -- "$file" | grep -q "^+.*@pytest.mark.ported_from"; then
        FILTERED_FILES="$FILTERED_FILES $file"
    fi
done

if [[ -z "$FILTERED_FILES" ]]; then
    echo "No new ported_from markers found."
    echo "any_ported=false" >> "$GITHUB_OUTPUT"
    exit 0
fi

uv run fill $FILTERED_FILES --show-ported-from --clean --quiet --links-as-filled --skip-coverage-missed-reason --ported-from-output-file ported_from_files.txt
files=$(cat ported_from_files.txt)
echo "Extracted converted tests:"
echo "$files"

if [[ -z "$files" ]]; then
    echo "No ported fillers found, check updates instead."
    echo "any_ported=false" >> "$GITHUB_OUTPUT"
    exit 0
fi

echo "any_ported=true" >> "$GITHUB_OUTPUT"

echo "----------------"
echo "Discovered existing json tests that will be BASE files:"

BASE_TESTS_PATH="${WORKSPACE_PATH}/evmtest_coverage/coverage/BASE_TESTS"
mkdir -p "$BASE_TESTS_PATH"

for file in $files; do
    # Make sure each file exist at least in develop or legacy tests
    file_found=0

    if [[ "$file" == *"BlockchainTests"* ]]; then
        destination_path="$BASE_TESTS_PATH/blockchain_tests"
    elif [[ "$file" == *"GeneralStateTests"* ]]; then
        destination_path="$BASE_TESTS_PATH/state_tests"
    else
        echo "Error: $file is not a valid test file"
        exit 1
    fi


    # Try ethereum/tests
    source_path="${WORKSPACE_PATH}/testpath/$file"
    if [ -e "$source_path" ]; then
        file_found=1
        mkdir -p "$destination_path"
        cp "$source_path" "$destination_path"
        echo "$source_path -> $destination_path"
    fi

    # Try ethereum/legacytests
    source_path="${WORKSPACE_PATH}/legacytestpath/Cancun/$file"
    base_name=$(basename "$file")
    legacy_file_name="legacy_$base_name"
    if [ -e "$source_path" ]; then
        file_found=1
        mkdir -p "$destination_path"
        cp "$source_path" "$destination_path/$legacy_file_name"
        echo "$source_path -> $destination_path"
    fi

    if [ $file_found -eq 0 ]; then
        echo "Error: Failed to find the test file $file in test repo"
        exit 1
    fi
done

exit 0