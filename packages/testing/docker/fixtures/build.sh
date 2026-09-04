#!/usr/bin/env sh
# Build a fixture image for one hive simulator.
#
#   packages/testing/docker/fixtures/build.sh <release-url|tarball|fixtures-dir> <format> <image-ref> [docker build args...]
#
#   <release-url>   URL of a release tarball, e.g.
#                   https://github.com/ethereum/execution-specs/releases/download/tests@v20.0.2/fixtures.tar.gz
#   <tarball>       a release tarball on disk, e.g. the fixtures_<sha> artifact of a nightly fill
#   <fixtures-dir>  an extracted release: the directory that contains .meta/
#                   and the fixture format directories
#   <format>        fixture directory to include, e.g. blockchain_tests_engine
#   <image-ref>     tag for the resulting image, e.g. fixtures/blockchain_tests_engine:v20.0.2
#
# Only .meta/ and <format>/ are handed to docker as the `fixtures` build
# context. A tarball is extracted selectively; a directory is staged with hard
# links, so multi-gigabyte fixture sets are not copied. Provenance is taken
# from the environment when set: EEST_FIXTURES_RELEASE, EEST_FIXTURES_GIT_SHA,
# EEST_REPOSITORY.
set -eu

if [ $# -lt 3 ]; then
    sed -n '2,18p' "$0" >&2
    exit 2
fi
source=$1
format=$2
image=$3
shift 3
here=$(cd "$(dirname "$0")" && pwd)

extract() {
    # Release tarballs have a single top-level directory; strip it and
    # extract only the metadata and the requested format.
    tar -xz -C "$stage" --strip-components=1 --wildcards "*/.meta/*" "*/$format/*"
}

case "$source" in
http://* | https://*)
    stage=$(mktemp -d "${TMPDIR:-/tmp}/eest-fixtures.XXXXXX")
    trap 'rm -rf "$stage"' EXIT INT TERM
    echo "downloading $source" >&2
    curl -fsSL "$source" | extract
    ;;
*.tar.gz | *.tgz)
    if [ ! -f "$source" ]; then
        echo "error: $source is not a file" >&2
        exit 1
    fi
    stage=$(mktemp -d "${TMPDIR:-/tmp}/eest-fixtures.XXXXXX")
    trap 'rm -rf "$stage"' EXIT INT TERM
    extract < "$source"
    ;;
*)
    if [ ! -f "$source/.meta/index.json" ]; then
        echo "error: $source has no .meta/index.json" >&2
        exit 1
    fi
    if [ ! -d "$source/$format" ]; then
        echo "error: $source has no $format/ directory" >&2
        exit 1
    fi
    # Stage next to the source so that hard links stay on one filesystem.
    stage=$(mktemp -d "$(dirname "$source")/.eest-fixtures-stage.XXXXXX")
    trap 'rm -rf "$stage"' EXIT INT TERM
    cp -al "$source/.meta" "$stage/.meta"
    cp -al "$source/$format" "$stage/$format"
    ;;
esac

for var in EEST_FIXTURES_RELEASE EEST_FIXTURES_GIT_SHA EEST_REPOSITORY; do
    eval "value=\${$var:-}"
    if [ -n "$value" ]; then
        set -- "$@" --build-arg "$var=$value"
    fi
done

DOCKER_BUILDKIT=1 docker build -f "$here/Dockerfile" \
    --build-context "fixtures=$stage" \
    --build-arg "format=$format" \
    -t "$image" "$@" "$here"
