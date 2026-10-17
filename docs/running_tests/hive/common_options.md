# Common Simulator Options

All execution-specs (EELS) Hive simulators share common command-line options and patterns.

## Basic Usage

The default Dockerfiles run published simulator images. Hive accepts short simulator names: `--sim consume-engine` selects `ethereum/eels/consume-engine`. Select the tests with `tag`; omit it for `latest`, the latest mainnet release. See [Choose a tag](images/index.md#choose-a-tag) for mainnet, devnet, release and nightly options.

For example, this selects the published image for the [`tests@v20.0.2` release](../releases.md#test-release-types):

```bash
./hive --sim consume-engine \
  --sim.buildarg tag=v20.0.2 \
  --client go-ethereum
```

Add `--docker.pull` to refresh an image already cached locally. A release tag fixes the tests; [pin a digest](images/how_to.md#reproduce-a-run-exactly) to fix the entire image.

The old `fixtures` and `branch` build arguments require `Dockerfile.git`, selected through `--sim.file`; see [Build from source](images/how_to.md#build-from-source-with-dockerfilegit). They are ignored by the default Dockerfiles.

## Test Selection

Run a subset of tests by filtering tests using `--sim.limit=<regex>` to perform a regular expression match against test IDs:

```bash
./hive --sim consume-engine --sim.limit ".*eip4844.*"
```

### Collect Only/Dry-Run

The `collectonly:` prefix can be used to inspect which tests would match an expression (dry-run), `--docker.output` must be specified to see the simulator's collection result:

```bash
./hive --sim consume-engine \
     --sim.buildarg tag=v20.0.2 \
     --docker.output \
     --sim.limit="collectonly:.*eip4844.*"
```

### Exact test ID Match

The `id:` prefix can be used to select a single test via its ID (this will automatically escape any special characters in the test case ID):

```console
./hive --sim consume-engine \
     --sim.buildarg tag=v20.0.2 \
     --docker.output \
     --sim.limit "id:tests/cancun/eip4844_blobs/test_blob_txs.py::test_sufficient_balance_blob_tx"
```

### Parallelism

To run multiple tests in parallel, use `--sim.parallelism`:

```bash
./hive --sim consume-rlp --sim.parallelism 4
```

### Output Options

See hive log output in the console:

```bash
./hive --sim consume-engine --sim.loglevel 5
```

### Container Issues

Increase client timeout:

```bash
./hive --client.checktimelimit=180s --sim consume-engine
```
