# Fixture image: a single fixture format from an execution-spec-tests release,
# with a matching .meta/index.json, under /fixtures. Published as
# ghcr.io/ethereum/execution-specs/fixtures/<format>:<release>. The image has
# no filesystem of its own (FROM scratch): the hive simulator images use it as
# their base layer, and anything else can COPY --from it or mount it.
#
# Build with packages/testing/docker/fixtures/build.sh, which prepares the
# `fixtures` build context from a release tarball URL or an extracted release:
#
#   packages/testing/docker/fixtures/build.sh <url-or-dir> blockchain_tests_engine \
#       fixtures/blockchain_tests_engine:v20.0.2
#
# Requires BuildKit (named build contexts).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS meta
ARG format
COPY subset_index.py /subset_index.py
RUN --mount=type=bind,from=fixtures,source=.meta,target=/src/.meta \
    python3 /subset_index.py /src/.meta /out/.meta --format-dir "${format}"

FROM scratch
ARG format
COPY --from=fixtures ${format} /fixtures/${format}
COPY --from=meta /out/.meta /fixtures/.meta

# Provenance: the release, or nightly fill, and the commit that produced it.
ARG EEST_FIXTURES_RELEASE=""
ARG EEST_FIXTURES_GIT_SHA=""
ARG EEST_REPOSITORY="ethereum/execution-specs"
LABEL org.opencontainers.image.source="https://github.com/${EEST_REPOSITORY}" \
      org.opencontainers.image.revision="${EEST_FIXTURES_GIT_SHA}" \
      org.ethereum.eest.fixtures-release="${EEST_FIXTURES_RELEASE}"
