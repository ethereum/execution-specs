# Simulator Images

The `ethereum/eels/*` simulators in [ethereum/hive](https://github.com/ethereum/hive) can run from ready-to-run images under `ghcr.io/ethereum/execution-specs/hive/`. Each image contains the simulator and its test content. Hive pulls the image and builds a small wrapper; it does not clone execution-specs, install Python dependencies or extract a fixture tarball during the simulator build.

**A simulator tag selects the tests.** Consume images contain a release's generated fixtures; execute images contain the Python test sources from the release commit. Images for a branch's current release receive framework updates on branch pushes. Older releases retain their last framework build. Nightly images use the fill commit for both tests and framework.

## Choose a tag

Pass a tag with `--sim.buildarg tag=<tag>`. These examples illustrate the publishing scheme; a tag is usable once its branch and release have been [published](../../../dev/publishing_images.md#first-rollout).

| To run | Use | What changes |
| --- | --- | --- |
| The latest mainnet release | `latest` (default) | Tests advance with releases; framework follows the default branch. |
| One devnet | `glamsterdam-devnet-8` | Tests advance within devnet 8; framework follows `devnets/glamsterdam/8`. |
| The newest devnet in a series | `glamsterdam-devnet-latest` | Moves to devnet 9 when its first release is published. |
| A specific release | `glamsterdam-devnet-v8.1.4` or `v20.0.2` | Tests stay fixed; framework updates while this is the branch's current release. |
| The most recent nightly fill | `nightly` | Tests and framework advance together with each published fill. |
| An exact image from an earlier run | `<tag>@sha256:<digest>` | Neither tests nor framework changes. Requires the retained image digest. |

On a machine that has run Hive before, add **`--docker.pull`** to refresh a moving tag. Without it, Docker can reuse the locally cached image. See the [full tag reference](reference.md#tags) for release-name mappings, commit tags and the distinction between simulator and repository images.

## Run or build an image

- [Run a simulator](tutorial.md): build Hive, run a few tests, and read the source versions in the log.
- [Choose tags and reproduce runs](how_to.md): follow a devnet, pin tests or image bytes, and build combinations that are not published.
- [Image and tag reference](reference.md): image names, tags, options, provenance and build helpers.
- [How images are built](explanation.md): design choices, source compatibility, layer reuse and costs.

The simulator images combine a repository image (code and dependencies) with a fixture image or a release test-source image. These components are also published for local builds. [Publishing Simulator Images](../../../dev/publishing_images.md) covers the workflow and rollout.

## Migrate an existing Hive command

The image Dockerfiles accept `tag` in place of `fixtures` and `branch`. Those old build arguments are ignored by the image Dockerfiles. To keep building from a Git ref and selecting fixtures independently, choose `Dockerfile.git` through `--sim.file`; see [Build from source](how_to.md#build-from-source-with-dockerfilegit).
