# Tests image: the test sources of one release, the tests/ tree at the commit
# the release was built from, under /execution-specs/tests. Published as
# ghcr.io/ethereum/execution-specs/tests:<release>. The image has no filesystem
# of its own (FROM scratch). The execute simulator images copy the tree out of
# it, so that they run the tests of the selected release while their framework
# follows the branch head, the same way the consume simulator images carry a
# release's fixtures. See docs/running_tests/hive/images/.
#
# Build with packages/testing/docker/tests/build.sh from a git ref or from a
# checked-out tests/ directory:
#
#   packages/testing/docker/tests/build.sh tests@v20.0.2 tests:v20.0.2
FROM scratch
ARG EEST_TESTS_RELEASE=""
ARG EEST_TESTS_GIT_SHA=""
ARG EEST_REPOSITORY="ethereum/execution-specs"
LABEL org.opencontainers.image.source="https://github.com/${EEST_REPOSITORY}" \
      org.opencontainers.image.revision="${EEST_TESTS_GIT_SHA}" \
      org.ethereum.eest.tests-release="${EEST_TESTS_RELEASE}"
COPY . /execution-specs/tests
