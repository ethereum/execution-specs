#!/usr/bin/env sh
# Check a hive simulator image before it is published.
#
#   packages/testing/docker/hive/check.sh <simulator> <image-ref>
#
# A consume image must carry the fixture format it consumes: a non-empty
# index whose entries all point to files present in the image. An execute
# image carries the test sources of a release under a framework that may have
# moved on since; the check collects the simulator's tests with that
# framework, so that a source tree the framework can no longer load fails
# here rather than in every hive run. Any failure fails this script.
set -eu

if [ $# -ne 2 ]; then
    sed -n '2,11p' "$0" >&2
    exit 2
fi
simulator=$1
image=$2

case "$simulator" in
consume-rlp) format=blockchain_tests ;;
consume-engine) format=blockchain_tests_engine ;;
consume-enginex) format=blockchain_tests_engine_x ;;
consume-sync) format=blockchain_tests_sync ;;
execute-blobs) ;;
*)
    echo "error: unknown simulator '$simulator'" >&2
    exit 1
    ;;
esac

if [ -n "${format:-}" ]; then
    docker run --rm --entrypoint python3 -e "FORMAT=$format" "$image" -c '
import json, os, sys
root = "/fixtures"
fmt = os.environ["FORMAT"]
if not os.path.isdir(f"{root}/{fmt}"):
    sys.exit(f"error: {root}/{fmt} is missing")
index = json.load(open(f"{root}/.meta/index.json"))
cases = index["test_cases"]
if not cases:
    sys.exit("error: the index has no test cases")
formats = {case["json_path"].split("/", 1)[0] for case in cases}
if formats != {fmt}:
    sys.exit(f"error: the index covers {sorted(formats)}, expected [{fmt!r}]")
paths = [case["json_path"] for case in cases]
missing = [path for path in paths if not os.path.isfile(f"{root}/{path}")]
if missing:
    sys.exit(f"error: {len(missing)} index entries point to missing files, e.g. {missing[0]}")
print(f"ok: {len(cases)} test cases under {root}/{fmt}, every file present")
'
else
    # Collect with the entry point's own command and selection, so that the
    # check covers exactly the tests a hive run executes. Exit 5, "no tests
    # collected", fails the check. The summary line's count is not used: it
    # includes items that later collection hooks drop without reporting them
    # as deselected, so it stays in the thousands for a marker that selects
    # nothing. The node ids printed by --collect-only are counted instead.
    docker run --rm --entrypoint sh "$image" -c '
set -u
cd /execution-specs
# The image default, which a hive run without a fork argument uses.
fork=${FORK:-${EEST_DEFAULT_FORK:-}}
if [ -z "$fork" ]; then
    echo "error: the image has no default fork (EEST_DEFAULT_FORK)" >&2
    exit 1
fi
status=0
uv run --no-sync execute hive --collect-only -q --fork="$fork" \
    -m blob_transaction_test > /tmp/collect.log 2>&1 || status=$?
collected=$(grep -c "^tests/.*::" /tmp/collect.log || true)
if [ "$status" -eq 5 ] || { [ "$status" -eq 0 ] && [ "$collected" -eq 0 ]; }; then
    echo "error: no blob_transaction_test tests collected" >&2
    exit 1
fi
if [ "$status" -ne 0 ]; then
    tail -n 40 /tmp/collect.log >&2
    echo "error: collecting the release tests under the image framework failed (exit $status)" >&2
    exit 1
fi
echo "ok: $collected blob_transaction_test tests collected at $fork"
'
fi
