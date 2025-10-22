# Executing Tests on a Hive Local Network

Tests can be executed on a local hive-controlled single-client network by running the `execute hive` command.

## The `eest/execute-blobs` Simulator

The `blob_transaction_test` execute test spec sends blob transactions to a running client in order to verify its `engine_getBlobsVX` endpoint behavior. These tests can be run using:

```bash
./hive --client besu --client-file ./configs/osaka.yaml --sim ethereum/eest/execute-blobs
```

See [Hive](../hive/index.md) for help installing and configuring Hive.

## Running `execute` tests with Hive in Dev Mode

This command requires hive to be running in `--dev` mode:

```bash
./hive --dev --client go-ethereum
```

This will start hive in dev mode with the single go-ethereum client available for launching tests.

Then the tests can be executed by setting the `HIVE_SIMULATOR` environment variable

```bash
export HIVE_SIMULATOR=http://127.0.0.1:3000
```

and running:

```bash
uv run execute hive --fork=Cancun
```

If the command above leads to errors such as `ImportError: Error importing plugin "pytest_plugins.execute.rpc.hive": No module named 'hive.client'` run the following to fix it: `uv run eest clean --all`.

This will execute all available tests in the `tests` directory on the `Cancun` fork by connecting to the hive server running on `http://127.0.0.1:3000` and launching a single client with the appropriate genesis file.

The genesis file is passed to the client with the appropriate configuration for the fork schedule, system contracts and pre-allocated seed account.

All tests will be executed in the same network, in the same client, and serially, but when the `-n auto` parameter is passed to the command, the tests can also be executed in parallel.

One important feature of the `execute hive` command is that, since there is no consensus client running in the network, the command drives the chain by the use of the Engine API to prompt the execution client to generate new blocks and include the transactions in them.
