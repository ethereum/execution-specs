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
#   FORK                                execute-blobs; defaults to EEST_DEFAULT_FORK, the fork
#                                       the release was filled for, set when the image is built
#   SKIP_GENESIS_INIT                   engine and enginex; 0 passes --no-skip-genesis-init, so
#                                       clients initialize the genesis in a separate step
set -eu

# Deprecated build arguments applied by eels-legacy-build (legacy_build.sh):
# run what they selected, and drop the image's provenance that no longer
# describes it, so that the log header stays truthful.
legacy=${EELS_LEGACY_STATE:-/etc/eels-simulator/legacy}
if [ -d "$legacy" ]; then
    echo "eels-simulator: deprecated build arguments fixtures/branch in use;" \
        "pass --sim.buildarg tag=<tag> instead, see ethereum/execution-specs#3866" >&2
    if [ -f "$legacy/fixtures" ]; then
        FIXTURES=$(cat "$legacy/fixtures")
        unset EEST_FIXTURES_RELEASE
    fi
    if [ -f "$legacy/branch" ]; then
        # The framework, and an execute image's tests, come from the branch.
        EEST_GIT_SHA=$(cat "$legacy/commit")
        EEST_GIT_REF=$(cat "$legacy/branch")
        export EEST_GIT_SHA EEST_GIT_REF
        unset EEST_TESTS_RELEASE EEST_TESTS_GIT_SHA
    fi
fi

cd /execution-specs/packages/testing
skip_genesis_init=
if [ "${SKIP_GENESIS_INIT-1}" = "0" ]; then
    skip_genesis_init=--no-skip-genesis-init
fi
case "${EEST_SIMULATOR:-}" in
consume-engine)
    exec uv run --no-sync consume engine -v --input "$FIXTURES" \
        --disable-strict-exception-matching "${DISABLE_STRICT_EXCEPTION_MATCHING-nimbus-el}" \
        $skip_genesis_init "$@"
    ;;
consume-enginex)
    exec uv run --no-sync consume enginex -v --input "$FIXTURES" \
        --disable-strict-exception-matching "${DISABLE_STRICT_EXCEPTION_MATCHING-nimbus-el}" \
        $skip_genesis_init "$@"
    ;;
consume-rlp)
    exec uv run --no-sync consume rlp -v --input "$FIXTURES" "$@"
    ;;
consume-sync)
    exec uv run --no-sync consume sync -v --input "$FIXTURES" "$@"
    ;;
execute-blobs)
    fork=${FORK:-${EEST_DEFAULT_FORK:-}}
    if [ -z "$fork" ]; then
        echo "eels-simulator: no fork; set FORK (--sim.buildarg fork=<fork>)" >&2
        exit 2
    fi
    # `execute` collects the tests from the source tree: run from the repository root.
    cd /execution-specs
    exec uv run --no-sync execute hive --fork="$fork" -v -m blob_transaction_test "$@"
    ;;
*)
    echo "eels-simulator: unknown or unset EEST_SIMULATOR '${EEST_SIMULATOR:-}'" >&2
    exit 2
    ;;
esac
