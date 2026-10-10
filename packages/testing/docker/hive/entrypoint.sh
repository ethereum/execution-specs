#!/bin/sh
# Entry point of the eels hive simulator images. EEST_SIMULATOR, set when the
# image is built, selects the command; extra arguments are passed through.
#
# Overridable at run time (hive passes environment variables from its
# --sim.buildarg values through the simulator Dockerfile):
#   FIXTURES                            fixture directory, /fixtures in the image
#   DISABLE_STRICT_EXCEPTION_MATCHING   engine and enginex; defaults to nimbus-el when
#                                       unset; an empty value exempts no client
#                                       TODO: remove when fixed on nimbus-el side.
#   FORK                                execute-blobs; defaults to Osaka
set -eu

cd /execution-specs/packages/testing
case "${EEST_SIMULATOR:-}" in
consume-engine)
    exec uv run --no-sync consume engine -v --input "$FIXTURES" \
        --disable-strict-exception-matching "${DISABLE_STRICT_EXCEPTION_MATCHING-nimbus-el}" "$@"
    ;;
consume-enginex)
    exec uv run --no-sync consume enginex -v --input "$FIXTURES" \
        --disable-strict-exception-matching "${DISABLE_STRICT_EXCEPTION_MATCHING-nimbus-el}" "$@"
    ;;
consume-rlp)
    exec uv run --no-sync consume rlp -v --input "$FIXTURES" "$@"
    ;;
consume-sync)
    exec uv run --no-sync consume sync -v --input "$FIXTURES" "$@"
    ;;
execute-blobs)
    # `execute` collects the tests from the source tree: run from the repository root.
    cd /execution-specs
    exec uv run --no-sync execute hive --fork="${FORK:-Osaka}" -v -m blob_transaction_test "$@"
    ;;
*)
    echo "eels-simulator: unknown or unset EEST_SIMULATOR '${EEST_SIMULATOR:-}'" >&2
    exit 2
    ;;
esac
