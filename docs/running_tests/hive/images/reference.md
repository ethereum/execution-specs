# Simulator Images Reference

## What a tag selects

A simulator tag selects test content. The framework revision depends on whether the tag is a release tag, a channel or `nightly`:

| Simulator | Test content |
| --- | --- |
| `consume-*` | Generated fixtures from the selected release or nightly fill. |
| `execute-*` | Python test sources at the commit that produced the release or fill. |

The same release tag on `hive/consume-engine` and `hive/execute-blobs` names the same release, although the simulators run different workloads. Framework updates include client exception mappings.

- **Release tags** (`v20.0.2`, `glamsterdam-devnet-v8.1.4`) are immutable. The release run publishes them once, with the framework at the head of the release's branch at that time, and never overwrites them.
- **Channel tags** (`latest`, `glamsterdam-devnet-8`) select a branch's highest release and receive framework updates when the branch moves. They are the tags that pick up fixes such as client exception mappings. Superseded pushes are skipped; the current head is built.
- **`nightly`** uses fixtures, test sources and framework from the fill commit. A failed or skipped fill does not advance it.

Other pairings can be [assembled locally](how_to.md#assemble-a-combination-that-is-not-published).

Every simulator image is checked before publication. A failed check leaves that simulator's tags unchanged; other image jobs may still publish successfully.

## Images

| Image | Contents | Built |
| --- | --- | --- |
| `ghcr.io/ethereum/execution-specs` | The repository: the execution-specs source tree, test sources included, and its synced virtualenv. Tagged `sha-<commit>` only. | On current pushes to `forks/**` or `devnets/**`; at the selected branch head for a release; at the fill commit for a nightly. |
| `ghcr.io/ethereum/execution-specs/fixtures/<format>` | One fixture format of one release or nightly fill under `/fixtures`, with `.meta/index.json` filtered to that format. No filesystem otherwise. Tagged by release and `nightly` only. | When a fixture release is published and after every nightly fill, one image per format. |
| `ghcr.io/ethereum/execution-specs/tests` | The `tests/` tree at the commit that produced a release or fill, under `/execution-specs/tests`. No filesystem otherwise. Tagged by release and `nightly` only. | When a fixture release is published and after every nightly fill. |
| `ghcr.io/ethereum/execution-specs/hive/<simulator>` | A ready-to-run simulator: the repository image with the fixtures or test sources of a release or fill. | On current pushes, for the branch's current release; when a release is published; after every nightly fill. |

Only the simulator images are a stable interface. The repository, fixture and tests images are their building blocks; their tags may change. The namespace below the repository names the runner: `hive/` for hive simulators, with room for further families such as direct test runners. The leaf of a hive image is the simulator directory name in ethereum/hive.

## Simulators and their test content

| Simulator | Image | Command | Test content |
| --- | --- | --- | --- |
| `consume-rlp` | `hive/consume-rlp` | `consume rlp` | `blockchain_tests` fixtures |
| `consume-engine` | `hive/consume-engine` | `consume engine` | `blockchain_tests_engine` fixtures |
| `consume-enginex` | `hive/consume-enginex` | `consume enginex` | `blockchain_tests_engine_x` fixtures, pre-alloc groups included |
| `consume-sync` | `hive/consume-sync` | `consume sync` | `blockchain_tests_sync` fixtures |
| `execute-blobs` | `hive/execute-blobs` | `execute hive -m blob_transaction_test` | the test sources of the release or fill |

## Tags

Mainnet release tags drop the `tests@` prefix. Devnet release tags drop `tests-` and replace `@` with `-`. Both full release names and friendly devnet names are accepted by `consume --input`:

| GitHub release | `consume --input` | Image tag |
| --- | --- | --- |
| `tests@v20.0.2` | `tests@v20.0.2` | `v20.0.2` |
| `tests-glamsterdam-devnet@v8.1.4` | `tests-glamsterdam-devnet@v8.1.4` or `glamsterdam-devnet@v8.1.4` | `glamsterdam-devnet-v8.1.4` |

Channels select releases automatically. The examples use `devnets/glamsterdam/8` and the repository's default branch for the mainnet line:

| Tag | Selects | Moves |
| --- | --- | --- |
| `v20.0.2`, `glamsterdam-devnet-v8.1.4` | That release's tests, with the framework of its release run. | never |
| `latest` | The highest mainnet release, as `consume --input tests@latest`, with the head of the default branch. | on pushes and higher releases |
| `glamsterdam-devnet-8` | The highest devnet-8 release with the head of `devnets/glamsterdam/8`. | on pushes and higher devnet-8 releases |
| `nightly` | The most recently published nightly fill; tests and framework from one commit. | after each successful fill |

These four forms are the tags of the simulator images. The fixture and tests images carry the release tags and `nightly`, which the simulator builds use; the repository image carries `sha-<commit>`. Devnet branch channels and `nightly` have no `consume --input` release counterpart. Tag examples describe the naming scheme; publication is enabled [branch by branch](../../../dev/publishing_images.md#first-rollout).

Rules behind the table:

- `latest` resolves exactly as `consume --input tests@latest` does: the highest published mainnet release that has a fixtures tarball, whatever its GitHub pre-release flag. Channel tags follow the highest version, never the newest publication, so a late 8.1.5 patch published after 9.0.0 moves only `glamsterdam-devnet-8`.
- `glamsterdam-devnet-8` is to devnet 8 what `latest` is to the default branch: the highest release of the branch with the head of the branch. A dashboard that follows a devnet uses it and switches to `glamsterdam-devnet-9` when devnet 9 starts.
- A release tag is written once. A re-run of a release run, manual or not, leaves an existing release tag unchanged and only moves the channel. To run a release with newer framework fixes, use its branch's channel while the release is the highest, or [assemble the pair](how_to.md#assemble-a-combination-that-is-not-published).
- No tag on any image is named after a fork, because the default branch is renamed at every fork. The default branch's channel is `latest`.
- Only the default branch publishes the mainnet tags, and a release is only ever paired with the branch it was cut from.
- The nightly fill covers the main line only, so `nightly` is a mainnet channel. Only the latest fill is tagged; the simulator log header and the image labels name the fill by its commit, `nightly-<commit>`, and the publishing run records its digest. Should the fill ever cover devnet branches, their nightly would be `glamsterdam-devnet-8-nightly`.
- The five simulator images move independently: a failed build leaves one image's channel tag on the previous release while the others advance.
- Channel tags and `nightly` name sources, not bytes: they are pushed again whenever their sources are rebuilt. A release tag keeps the bytes its release run published. The byte-exact identity of an image is its digest, `ghcr.io/ethereum/execution-specs/hive/consume-engine@sha256:…`, which the publishing run records; see [Reproduce a run exactly](how_to.md#reproduce-a-run-exactly).

## Hive build arguments

Set with `--sim.buildarg name=value` on the image Dockerfiles. For the separate `branch` and `fixtures` arguments of `Dockerfile.git`, see [Build from source](how_to.md#build-from-source-with-dockerfilegit).

| Argument | Simulators | Default | Purpose |
| --- | --- | --- | --- |
| `tag` | all | `latest` | Selects the tests, see Tags. Accepts `<tag>@sha256:<digest>` to pin an exact image. |
| `image` | all | the simulator's published image | Another registry namespace or a locally built image. |
| `disable_strict_exception_matching` | `consume-engine`, `consume-enginex` | `nimbus-el` | Clients exempt from strict exception matching; an empty value exempts none. |
| `fork` | `execute-blobs` | `Osaka` | Fork to execute the tests for. |

## Variables and labels set in the images

These belong to the images, not to the testing package: the Dockerfiles set them when an image is built, and the entry point reads them when a container starts. The package reads only the provenance ones for its log headers, `EEST_GIT_SHA` as `consume ref` and `execute ref`, `EEST_FIXTURES_RELEASE` as `fixtures release`, and `EEST_TESTS_RELEASE` and `EEST_TESTS_GIT_SHA` as `tests release` and `tests ref`, so that a log names what ran.

| Variable | Label | Meaning |
| --- | --- | --- |
| `EEST_SIMULATOR` | `org.ethereum.eest.simulator` | Simulator the entry point runs. Simulator images only. |
| `EEST_GIT_SHA` | `org.opencontainers.image.revision` | Commit of the simulator and framework code. On a fixture or tests image, the commit of the release or fill. |
| `EEST_GIT_REF` | `org.opencontainers.image.version` | Branch the code was taken from. |
| `EEST_FIXTURES_RELEASE` | `org.ethereum.eest.fixtures-release` | Release of the fixtures, for example `tests@v20.0.2`, or `nightly-<commit>` for a fill. Consume and fixture images. |
| `EEST_TESTS_RELEASE` | `org.ethereum.eest.tests-release` | Release of the test sources, or `nightly-<commit>`. Execute and tests images. |
| `EEST_TESTS_GIT_SHA` | `org.ethereum.eest.tests-revision` | Commit the test sources were taken from. Execute and tests images. |
| `FIXTURES` | | `/fixtures`, the fixture directory the entry point passes to `consume`. |

Fixture and tests images contain data and labels only; they do not set runtime environment variables. The tests image records its source commit as `org.opencontainers.image.revision`; the execute simulator also records it as `org.ethereum.eest.tests-revision`.

Read by the entry point at run time: `DISABLE_STRICT_EXCEPTION_MATCHING`, `FORK`, and the `HIVE_*` variables hive sets.

## Files

All under `packages/testing/`.

| Path | Purpose |
| --- | --- |
| `docker/base/Dockerfile` | The repository image. Context is the repository root. |
| `docker/base/Dockerfile.dockerignore` | Build context of the repository image: excludes `.git`, virtualenvs, caches, generated fixtures, logs, docs and worktrees. Read by BuildKit from beside the Dockerfile. |
| `docker/fixtures/Dockerfile` | A fixture image. Takes the extracted release as the named build context `fixtures` and the format as build argument `format`; labelled with the release and its commit. |
| `docker/fixtures/build.sh` | `build.sh <url, tarball or dir> <format> <image>`: prepares the build context from a release tarball URL, a tarball on disk such as a nightly artifact, or an extracted release, and builds the image. |
| `docker/fixtures/subset_index.py` | `subset_index.py <src .meta> <dst .meta> --format-dir <dir>`: writes the `.meta` directory of a subset with `index.json` filtered and `test_count`, `fixture_formats` and `forks` recomputed. `root_hash` is cleared. |
| `docker/tests/Dockerfile` | The tests image: a `tests/` tree under `/execution-specs/tests`. |
| `docker/tests/build.sh` | `build.sh <git ref or tests dir> <image>`: exports the `tests/` tree of a release tag with `git archive`, or takes a checked-out directory, and builds the image. |
| `docker/hive/Dockerfile` | A consume simulator image. Build arguments `BASE_REF`, `FIXTURES_REF`, `EEST_SIMULATOR`, and the provenance arguments above. |
| `docker/hive/Dockerfile.execute` | An execute simulator image: the repository image with its `tests/` replaced by a tests image. Build arguments `BASE_REF`, `TESTS_REF`, `EEST_SIMULATOR`, and the provenance arguments. |
| `docker/hive/build.sh` | `build.sh <simulator> <base ref> <registry> <tag> <image>`: picks the Dockerfile and the fixture or tests image for the simulator and builds it. `-` as the registry names local images. Provenance is taken from the environment. |
| `docker/hive/check.sh` | `check.sh <simulator> <image>`: verifies a built image before it is published. A consume image must carry a non-empty index whose entries all point to files in the image; an execute image must collect the release's tests under the image's framework. |
| `docker/hive/entrypoint.sh` | Entry point of the hive simulator images, installed as `eels-simulator`. Selects the command from `EEST_SIMULATOR`. |
| `src/execution_testing/tools/docker_images.py` | The image catalogue and every naming rule: branch tags, release names, which branch a release belongs to, the channel tags a release holds, and the tags each image receives. `plan()` computes a publishing run. |
| `src/execution_testing/tools/tests/test_docker_images.py` | Tests of the naming rules and the plan. |
| `src/execution_testing/cli/eest/commands/images.py` | The `eest images` command. |

## The `eest images` command

`eest images branch-tag <branch>` prints the branch tag of a branch; `eest images release-branch <release> --default-branch <branch>` prints the branch a release was cut from.

`eest images plan --sha <commit> --default-branch <branch> [--branch <branch>] [--release <tag> | --nightly] [--repository <owner/name>] [--release-repository <owner/name>] [--resolve-commits] [--github]` prints, as JSON, what a publishing run builds. With `--branch` alone, a push: the repository image of the head and the simulator images of the branch's current release. With `--release`, the fixture images and the tests image of the release and the simulator images pairing it with the head of the branch it was cut from, which is inferred from the tag and checked against `--branch` when given. With `--nightly`, every image at the fill commit `--sha` under the nightly tags. `--resolve-commits` resolves the release's commit from its git tag; `--github` joins the tag lists into space-separated strings for shell steps. The publishing workflow runs it once and feeds every other job from its output; see [Publishing Simulator Images](../../../dev/publishing_images.md).
