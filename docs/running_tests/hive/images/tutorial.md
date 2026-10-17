# Run a Simulator from the Published Images

This tutorial runs the `consume-rlp` simulator against go-ethereum from the published images, reads what ran, and then runs a devnet. It takes about ten minutes, most of it the first image pull.

## Prerequisites

- Docker with the daemon running.
- Go 1.24 or newer, matching the [Hive go.mod](https://github.com/ethereum/hive/blob/master/go.mod) requirement.
- About 6 GB of free disk space for the images.
- A Hive revision with the image Dockerfiles and a published `consume-rlp:latest` image. Image support is rolled out per branch; see [Publishing Simulator Images](../../../dev/publishing_images.md#first-rollout).

## Build hive

```bash
git clone https://github.com/ethereum/hive
cd hive
go build .
```

## Run the simulator

Every eels simulator defaults to the tag `latest`: the tests of the latest mainnet release, the one `consume --input tests@latest` resolves, run by the simulator code at the head of the default branch of execution-specs. Limit the run to a handful of tests with `--sim.limit`. It takes a regular expression that must match the whole test id, so start it with `.*`:

```bash
./hive --sim consume-rlp --client go-ethereum \
    --sim.limit '.*test_push0\.py.*fork_Prague.*' \
    --docker.pull --docker.buildoutput
```

!!! warning "Refresh images before testing a moving tag"

    Without `--docker.pull`, Docker can reuse an older local image even when its tag is `latest` or a devnet channel. Include this flag to refresh the base images for **both clients and simulators**. It also applies when selecting simulators with `--sim.file`.

    If a Dockerfile fetches code during the build, such as a client or simulator `Dockerfile.git`, also disable the build cache so those steps run again. Add `--docker.nocache '^hive/clients/'` for client builds, or `--docker.nocache '.*'` for all builds. This flag takes a regular expression; it does not replace `--docker.pull`. Rebuilding from source can take considerably longer.

    For a dashboard reproduction, use the recorded versions and [pin the simulator image digest](how_to.md#reproduce-a-run-exactly) instead of following a moving tag.

Hive pulls `ghcr.io/ethereum/execution-specs/hive/consume-rlp:latest`, about 550 MB compressed, and `ethereum/client-go:latest`, builds the simulator and client images in a few seconds, and runs the tests. The run ends with a line like:

```text
simulation ethereum/eels/consume-rlp finished suites=1 tests=16 failed=0
```

## Read what ran

The simulator log in the results directory, `workspace/logs/*-simulator-*.log`, starts with a header that names the code and the fixtures:

```text
consume ref: 027634bfd03cfa5dfa7f26351e881339cf2a0067
fixtures: /fixtures
fixtures release: tests@v20.0.2
```

`fixtures release` is the release whose tests ran and `consume ref` is the execution-specs commit the simulator code came from. An execute simulator prints `tests release` and `tests ref` for the same purpose. Together they identify the source versions. An image digest identifies the exact image bytes; see [Reproduce a run exactly](how_to.md#reproduce-a-run-exactly).

## Run a devnet

Once its images have been published, a tag can also name a devnet. `glamsterdam-devnet-8` runs the tests of the highest devnet-8 release with the simulator code at the head of `devnets/glamsterdam/8`:

```bash
./hive --sim consume-engine --client go-ethereum \
    --sim.buildarg tag=glamsterdam-devnet-8 \
    --sim.limit '.*eip7928.*' --docker.pull
```

## View the results

```bash
go build ./cmd/hiveview
./hiveview --serve --logdir workspace/logs
```

Open <http://127.0.0.1:8080> in a browser.

## Where to go next

The [how-to guides](how_to.md) cover following a devnet, running last night's fill, pinning a release, reproducing a run exactly and building the images yourself. The [reference](reference.md) lists every image and tag form.
