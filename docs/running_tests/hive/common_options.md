# Common Simulator Options

All EEST Hive simulators share common command-line options and patterns.

## Basic Usage

While they may be omitted, it's recommended to specify the `fixtures` and `branch` simulator build arguments when running EEST simulators.

For example, this runs "stable" fixtures from the v4.3.0 [latest stable release](../releases.md#standard-releases) and builds the simulator at the v4.3.0 tag:

```bash
./hive --sim ethereum/eest/consume-engine \
  --sim.buildarg fixtures=stable@v4.3.0 \
  --sim.buildarg branch=v4.3.0 \
  --client go-ethereum
```

## Test Selection

Run a subset of tests by filtering tests using `--sim.limit=<regex>` to perform a regular expression match against test IDs:

```bash
./hive --sim ethereum/eest/consume-engine --sim.limit ".*eip4844.*"
```

### Collect Only/Dry-Run

The `collectonly:` prefix can be used to inspect which tests would match an expression (dry-run), `--docker.output` must be specified to see the simulator's collection result:

```bash
./hive --sim ethereum/eest/consume-engine \
     --sim.buildarg fixtures=stable@v4.3.0 \
     --sim.buildarg branch=v4.3.0 \
     --docker.output \
     --sim.limit="collectonly:.*eip4844.*"
```

### Exact test ID Match

The `id:` prefix can be used to select a single test via its ID (this will automatically escape any special characters in the test case ID):

```console
./hive --sim ethereum/eest/consume-engine \
     --sim.buildarg fixtures=stable@v4.3.0 \
     --sim.buildarg branch=v4.3.0 \
     --docker.output \
     --sim.limit "id:tests/cancun/eip4844_blobs/test_blob_txs.py::test_sufficient_balance_blob_tx"
```

### Parallelism

To run multiple tests in parallel, use `--sim.parallelism`:

```bash
./hive --sim ethereum/eest/consume-rlp --sim.parallelism 4
```

### Output Options

See hive log output in the console:

```bash
./hive --sim ethereum/eest/consume-engine --sim.loglevel 5
```

### Container Issues

Increase client timeout:

```bash
./hive --client.checktimelimit=180s --sim ethereum/eest/consume-engine
```
