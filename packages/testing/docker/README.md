# Docker images for the hive eels simulators

The `ethereum/eels/*` simulators in ethereum/hive run from images built here and published under `ghcr.io/ethereum/execution-specs`. A simulator tag selects the tests: generated fixtures for consume, or the release's Python test sources for execute. Images for a branch's current release receive framework updates; older releases keep their last build. Nightly images use the fill commit for both tests and framework.

Start with [Simulator Images](../../../docs/running_tests/hive/images/index.md), or jump to the [tag reference](../../../docs/running_tests/hive/images/reference.md#tags), [local build instructions](../../../docs/running_tests/hive/images/how_to.md#build-the-images-from-a-local-checkout) or [publishing guide](../../../docs/dev/publishing_images.md). Naming rules live in `execution_testing.tools.docker_images`, exposed through `eest images`.

| Directory | Image | Contents |
| --- | --- | --- |
| `base/` | `ghcr.io/ethereum/execution-specs:<tag>` | The repository: source tree and synced virtualenv, tagged `sha-<7>`, `latest` on the default branch, `<name>-devnet-<n>` on a devnet branch, `nightly` for a fill. Built from the repository root; `Dockerfile.dockerignore` limits the context. |
| `fixtures/` | `ghcr.io/ethereum/execution-specs/fixtures/<format>:<tag>` | One fixture format of one release or nightly fill, as a data-only image. `build.sh` prepares the build context from a release tarball URL, a tarball on disk or an extracted release; `subset_index.py` filters the index. |
| `tests/` | `ghcr.io/ethereum/execution-specs/tests:<tag>` | The test sources of one release or fill, `tests/` at its commit, as a data-only image. `build.sh` exports them from a git ref or takes a checked-out directory. |
| `hive/` | `ghcr.io/ethereum/execution-specs/hive/<simulator>:<tag>` | A ready-to-run simulator. `Dockerfile` flattens the repository image onto a fixture image; `Dockerfile.execute` replaces the repository image's `tests/` with a tests image. `build.sh` picks the right one per simulator; `check.sh` verifies an image before it is published. |
