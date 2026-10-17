# The repository as a docker image: the execution-specs source tree and its
# synced virtualenv, published as ghcr.io/ethereum/execution-specs with one tag
# per branch. It is the base of every image under packages/testing/docker and
# runs any command of the testing package on its own, for example:
#
#   docker run --rm ghcr.io/ethereum/execution-specs uv run --no-sync ethereum-spec-evm t8n --help
#
# Build from the repository root, so that the uv workspace is complete. The
# Dockerfile.dockerignore beside this file keeps generated fixtures, caches and
# worktrees out of the build context:
#
#   docker build -f packages/testing/docker/base/Dockerfile -t execution-specs:local .
#
# Fixtures are deliberately not part of this image; see ../fixtures.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# GitPython, used by EEST for version reporting, needs the git binary at import.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /execution-specs

# Third-party dependencies first: source-only changes reuse this layer.
COPY pyproject.toml uv.lock ./
COPY packages/testing/pyproject.toml packages/testing/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --directory packages/testing

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --directory packages/testing

# Provenance for published images: the copied tree carries no .git directory.
# ghcr uses the source label to link the package to the publishing repository.
ARG EEST_GIT_SHA=""
ARG EEST_GIT_REF=""
ARG EEST_REPOSITORY="ethereum/execution-specs"
LABEL org.opencontainers.image.source="https://github.com/${EEST_REPOSITORY}" \
      org.opencontainers.image.revision="${EEST_GIT_SHA}" \
      org.opencontainers.image.version="${EEST_GIT_REF}"
# EEST reports these instead of `git` output, which the image cannot provide.
ENV EEST_GIT_SHA=${EEST_GIT_SHA} \
    EEST_GIT_REF=${EEST_GIT_REF}

# The hive simulators run `consume` from here and read fixtures from /fixtures.
WORKDIR /execution-specs/packages/testing
ENV FIXTURES=/fixtures
