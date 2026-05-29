#!/usr/bin/env bash
# Run `fill` on tests/ported_static for Osaka with traces enabled, detached
# from the controlling terminal so it survives logout / harness timeouts.
#
# Used as the producer step for `scripts/detect_oog_by_design.py`.
#
# Usage:
#   scripts/fill_for_oog_detection.sh            # default: tests/ported_static, -n 6
#   scripts/fill_for_oog_detection.sh -n 3       # custom worker count
#   scripts/fill_for_oog_detection.sh tests/foo  # custom test path
#
# All temp files land under $HOME/.tmp (avoids filling tmpfs /tmp). Traces go
# to $HOME/.tmp/oog-traces; fixtures go to $HOME/.tmp/oog-fixtures.
#
# Monitor with:
#   tail -f $HOME/.tmp/oog-fill.log
#   grep -oE '\[ *[0-9]+/[0-9]+\]' $HOME/.tmp/oog-fill.log | tail -1
#
# When fill exits, run:
#   uv run scripts/detect_oog_by_design.py <test_path> \
#       --evm-dump-dir=$HOME/.tmp/oog-traces \
#       --output=oog-by-design.json

set -euo pipefail

TEST_PATH="${1:-tests/ported_static}"
shift || true
# Remaining args are forwarded verbatim to `fill` (e.g. -n 3, --fork Prague).
EXTRA_ARGS=("$@")
if [[ ${#EXTRA_ARGS[@]} -eq 0 ]]; then
    EXTRA_ARGS=(-n 2)
fi

DUMP_DIR="$HOME/.tmp/oog-traces"
FIXTURES_DIR="$HOME/.tmp/oog-fixtures"
LOG_FILE="$HOME/.tmp/oog-fill.log"

echo "Cleaning previous run state..."
rm -rf "$DUMP_DIR" "$FIXTURES_DIR" "$LOG_FILE"
mkdir -p "$DUMP_DIR" "$FIXTURES_DIR"

echo "Starting fill (detached)..."
setsid nohup bash -c "
  TMPDIR=\$HOME/.tmp uv run fill '$TEST_PATH' \\
    --fork Osaka \\
    --traces \\
    --evm-dump-dir='$DUMP_DIR' \\
    --output='$FIXTURES_DIR' \\
    ${EXTRA_ARGS[*]}
" > "$LOG_FILE" 2>&1 < /dev/null &
PID=$!
disown

echo "fill pid: $PID"
echo "log:      $LOG_FILE"
echo "traces:   $DUMP_DIR"
echo
echo "Monitor:"
echo "  tail -f $LOG_FILE"
echo "  grep -oE '\\[ *[0-9]+/[0-9]+\\]' $LOG_FILE | tail -1"
echo "  ps -p $PID"
