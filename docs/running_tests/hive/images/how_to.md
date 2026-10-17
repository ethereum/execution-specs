# Choose Tags, Reproduce Runs and Build Images

The guides assume Hive is built, as in [Run a Simulator](tutorial.md), and the selected tag has been published. `consume-engine` stands for any EELS simulator. Tag selection works the same for `execute-blobs`; source-build reproduction differs as described below. For a quick comparison, see [Choose a tag](index.md#choose-a-tag).

Hive accepts short names with `--sim`: `consume-engine` selects `ethereum/eels/consume-engine`. The `simulator:` field in a `--sim.file` YAML configuration requires the full name.

## Follow a devnet or the mainnet line

The channel tags follow the releases and the branch head together. `glamsterdam-devnet-8` runs the highest release of Glamsterdam devnet 8 with the head of `devnets/glamsterdam/8`, which is how a dashboard for that devnet is configured; `glamsterdam-devnet-latest` follows the highest release of any Glamsterdam devnet and so moves from devnet 8 to devnet 9 on its own; `latest`, the default, follows the highest mainnet release with the head of the default branch:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=glamsterdam-devnet-8

./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=glamsterdam-devnet-latest

./hive --sim consume-engine --client go-ethereum
```

## Run last night's fill

`nightly` runs the fixtures of the most recent nightly fill of the main line, with the test sources and framework from the same commit, so merged changes can be tested before the next release. A failed or skipped fill leaves the tag unchanged:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=nightly
```

`nightly-<commit>` names one fill exactly, by the seven-character prefix of the commit it built. The simulator log header reports it as `fixtures release: nightly-<commit>`.

## Pin a release

Name the release. The simulator runs exactly the tests of that release. While the release is the current one of its branch, the framework follows the branch head; once a newer release exists, the tag keeps the framework of its last build:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=v20.0.2

./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=glamsterdam-devnet-v8.1.4
```

Mainnet tags drop `tests@`; devnet tags drop `tests-` and replace `@` with `-`. See the [release-name mapping](reference.md#tags).

## Refresh a moving tag

Docker can reuse an older local image behind a moving tag. Use `--docker.pull` to refresh the base images for both clients and simulators, including simulators selected with `--sim.file`:

```bash
./hive --sim consume-engine --client go-ethereum \
    --docker.pull
```

For Dockerfiles that fetch code during the build, also disable the build cache to fetch the current sources. Add `--docker.nocache '^hive/clients/'` to rebuild clients, or `--docker.nocache '.*'` to rebuild all images. The argument is a regular expression matching Hive's built image names. Keep `--docker.pull` to refresh their base images too; disabling the cache alone does not do that.

## Reproduce a run exactly

The simulator log header names the sources of the image that ran: `consume ref` or `execute ref` is the framework commit, `fixtures release` or `tests release` the release. Use [Assemble a combination that is not published](#assemble-a-combination-that-is-not-published) to combine those source versions. Consume simulators can also [build that source pair with Dockerfile.git](#build-from-source-with-dockerfilegit). Execute images need the separate release test snapshot, which `Dockerfile.git` does not select.

Byte-exact reproduction needs the image's digest, because tags name sources rather than bytes and are pushed again when the same sources are rebuilt. On the machine that ran hive, right after the run:

```bash
docker image inspect \
    ghcr.io/ethereum/execution-specs/hive/consume-engine:latest \
    --format '{{index .RepoDigests 0}}'
```

The publishing run also records the digest of every tag it pushed in its step summary and its `digests-*` artifacts. Run the exact image by appending the digest to the tag:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=latest@sha256:0123abcd…
```

A digest stays pullable while the registry retains the image. No retention period is defined yet; [registry housekeeping](../../../dev/publishing_images.md#registry-housekeeping) is a follow-up. Keep a local copy if a run must remain reproducible independently of registry retention.

## Assemble a combination that is not published

Published simulator images pair each branch head with the branch's current release. Any other pair, such as an older release against a newer commit, or a release against a commit from another branch, can be assembled locally in about half a minute from the primitive images: the repository image has a `sha-` tag for each published framework build, and fixture and tests images have tags for published releases. Superseded pushes may have no repository image; build one from a checkout for such a commit.

1. Clone or update execution-specs. The build script is `packages/testing/docker/hive/build.sh`.
2. Pick the framework commit and the release. Commit: `ghcr.io/ethereum/execution-specs:sha-<7 hex>`, or a branch tag such as `ghcr.io/ethereum/execution-specs:glamsterdam-devnet-8`. Release: its tag as it appears on the images, for example `v20.0.1`. The script takes the fixture image of the simulator's format, or the tests image for an execute simulator, from the registry you name.
3. Build the image. Docker pulls the inputs if they are missing, the fixture image being the large one:

    ```bash
    packages/testing/docker/hive/build.sh consume-engine \
        ghcr.io/ethereum/execution-specs:sha-1a2b3c4 \
        ghcr.io/ethereum/execution-specs v20.0.1 \
        hive/consume-engine:mine
    ```

4. Run hive with your image, without `--docker.pull`, which would ask the registry for `hive/consume-engine:mine`:

    ```bash
    ./hive --sim consume-engine --client go-ethereum \
        --sim.buildarg image=hive/consume-engine \
        --sim.buildarg tag=mine
    ```

Set `EEST_GIT_SHA` and `EEST_FIXTURES_RELEASE`, or `EEST_TESTS_RELEASE` for an execute simulator, in the environment of the build command so that the simulator log header reports the pair you chose. For a commit that was never pushed, build the repository image from a checkout first, as in [Build the images from a local checkout](#build-the-images-from-a-local-checkout), and pass `execution-specs:local` as the code image.

## Build from source with Dockerfile.git

Use a source build when testing an unpublished branch or selecting consume fixtures independently of the framework. Save this as `simulators.yaml` in the Hive checkout:

```yaml
- simulator: ethereum/eels/consume-engine
  dockerfile: git
  build_args:
    branch: devnets/glamsterdam/8
    fixtures: tests-glamsterdam-devnet@v8.1.4
```

Run it with:

```bash
./hive --sim.file simulators.yaml --client go-ethereum
```

`branch` accepts a Git ref; use a full commit SHA to pin the framework source. `fixtures` is a `consume --input` value, such as a release name or URL, not an image tag. With these arguments omitted, source builds use the repository's default branch and `tests@latest`.

For `execute-blobs`, `Dockerfile.git` runs both the framework and tests from `branch`; it has no `fixtures` argument. To reproduce a release's test snapshot under a different framework commit, [assemble an execute image](#assemble-a-combination-that-is-not-published) or [pin the original image digest](#reproduce-a-run-exactly).

Existing `--sim.buildarg branch=...` and `fixtures=...` options require `dockerfile: git`. The default image Dockerfiles ignore them, so migrate to `tag` or select the source Dockerfile explicitly.

## Build the images from a local checkout

Use this when working on the simulator code or on the images.

The repository image is built from the repository root, because the uv workspace spans the whole tree. The `Dockerfile.dockerignore` beside the Dockerfile keeps generated fixtures, caches and worktrees out of the build context:

```bash
docker build -f packages/testing/docker/base/Dockerfile \
    -t execution-specs:local .
```

A fixture image holds one fixture format. Build it from a release URL, a release tarball on disk, or an extracted release, for example the directory `consume cache` keeps:

```bash
release_url=https://github.com/ethereum/execution-specs/releases/download
packages/testing/docker/fixtures/build.sh \
    "$release_url/tests@v20.0.2/fixtures.tar.gz" \
    blockchain_tests_engine fixtures/blockchain_tests_engine:v20.0.2

# Set this to an extracted release directory containing .meta/.
fixtures_dir=/path/to/extracted/fixtures
packages/testing/docker/fixtures/build.sh "$fixtures_dir" \
    blockchain_tests fixtures/blockchain_tests:v20.0.2
```

The helper hands only `.meta/` and the chosen format directory to docker, hard-linked rather than copied, and filters `index.json` to the kept cases. The `blockchain_tests` directory of `tests@v20.0.2` is 3.8 GB on disk and about 0.3 GB as an image layer in the registry.

The tests image holds the test sources of a release. Build it from the release tag, which must be fetched in your clone, or from a checked-out `tests/` directory:

```bash
packages/testing/docker/tests/build.sh tests@v20.0.2 tests:v20.0.2
```

A simulator image combines the repository image with the release's fixture or tests image. `-` as the registry names local images without a prefix, `fixtures/<format>:<release>` and `tests:<release>`:

```bash
packages/testing/docker/hive/build.sh consume-rlp \
    execution-specs:local - v20.0.2 hive/consume-rlp:local

packages/testing/docker/hive/build.sh execute-blobs \
    execution-specs:local - v20.0.2 hive/execute-blobs:local

packages/testing/docker/hive/check.sh execute-blobs hive/execute-blobs:local
```

Then run Hive with `--sim.buildarg image=hive/consume-rlp` and `--sim.buildarg tag=local`. The check script runs the same verification the publishing workflow runs before a push.

## Use the repository image as a tool image

The repository image runs every command of the testing package, including the EELS `t8n` and `statetest` tools, without a checkout:

```bash
docker run --rm ghcr.io/ethereum/execution-specs:latest \
    uv run --no-sync ethereum-spec-evm t8n --help

docker run --rm -v "$PWD:/work" -w /work \
    ghcr.io/ethereum/execution-specs:latest \
    uv run --no-sync --directory /execution-specs/packages/testing \
    ethereum-spec-evm statetest /work/test.json
```

## Use images from another registry namespace

When the images live under a fork, override the image as well as the tag:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg image=ghcr.io/<user>/execution-specs/hive/consume-engine \
    --sim.buildarg tag=<tag>
```

Private packages need `docker login ghcr.io` and hive's `--docker.auth` flag.

## Change simulator options

The entry point of the images reads a few environment variables, which hive sets from build arguments of the simulator Dockerfiles:

- `--sim.buildarg disable_strict_exception_matching=<client>` for `consume-engine` and `consume-enginex`, default `nimbus-el`; an empty value exempts no client.
- `--sim.buildarg fork=<fork>` for `execute-blobs`, default `Osaka`.

Test selection, parallelism and log level are hive options, see [Common Options](../common_options.md).
