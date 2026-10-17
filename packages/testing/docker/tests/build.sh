#!/usr/bin/env sh
# Build the tests image of a release: the tests/ tree at one commit.
#
#   packages/testing/docker/tests/build.sh <git-ref|tests-dir> <image-ref> [docker build args...]
#
#   <git-ref>    a release tag or commit of this repository, e.g. tests@v20.0.2;
#                the tests/ tree is exported from it with git archive
#   <tests-dir>  a checked-out tests/ directory
#   <image-ref>  tag for the result, e.g. tests:v20.0.2
#
# Provenance is taken from the environment when set: EEST_TESTS_RELEASE,
# EEST_REPOSITORY, and EEST_TESTS_GIT_SHA, which defaults to the resolved ref.
set -eu

if [ $# -lt 2 ]; then
    sed -n '2,12p' "$0" >&2
    exit 2
fi
source=$1
image=$2
shift 2
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)

if [ -d "$source" ]; then
    context=$source
    sha=${EEST_TESTS_GIT_SHA:-}
else
    sha=$(git -C "$root" rev-parse --verify "$source^{commit}")
    stage=$(mktemp -d "${TMPDIR:-/tmp}/eest-tests.XXXXXX")
    trap 'rm -rf "$stage"' EXIT INT TERM
    git -C "$root" archive "$source" tests | tar -x --strip-components=1 -C "$stage"
    context=$stage
fi

if [ -n "$sha" ]; then
    set -- "$@" --build-arg "EEST_TESTS_GIT_SHA=$sha"
fi
for var in EEST_TESTS_RELEASE EEST_REPOSITORY; do
    eval "value=\${$var:-}"
    if [ -n "$value" ]; then
        set -- "$@" --build-arg "$var=$value"
    fi
done

DOCKER_BUILDKIT=1 docker build -f "$here/Dockerfile" -t "$image" "$@" "$context"
