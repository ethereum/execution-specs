# Executing Tests on a Hive Local Network

Tests can be executed on a local hive-controlled single-client network by running the `execute hive` command.

## The `eels/execute-blobs` Simulator

The `blob_transaction_test` execute test spec sends blob transactions to a running client. Blob transactions are fully supported in execute mode:

- Blob transactions can be sent via `eth_sendRawTransaction`
- Blob validation via `engine_getBlobsVX` endpoints (when Engine RPC available)
- Automatic gas pricing is used for the blob gas fees

Tests can be run using:

```bash
./hive --client besu --client-file ./configs/osaka.yaml --sim ethereum/eels/execute-blobs
```

**Note**: If the Engine RPC is unavailable, blob transactions will be sent and `getBlobsV*` validation is skipped.

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

## Using `testing_buildBlockV1`

Clients that implement the `testing_buildBlockV1` endpoint can use it as an alternative to the standard Engine API block building flow. Instead of sending transactions to the mempool and building blocks through `engine_forkchoiceUpdatedVX` / `engine_getPayloadVX`, the plugin sends transactions directly inside the `testing_buildBlockV1` call, which builds a block containing exactly those transactions.

To enable this route, pass the `--use-testing-build-block` flag:

```bash
uv run execute hive --fork=Prague --use-testing-build-block
```

Or in dev mode:

```bash
./hive --dev --client go-ethereum
uv run execute hive --fork=Prague --use-testing-build-block
```

This is useful when:

- The client supports the endpoint and you want faster block building (the `--get-payload-wait-time` delay is skipped).
- You want deterministic transaction ordering in each block (transactions are included in the exact order provided).

See [Block Building with `testing_buildBlockV1`](./index.md#block-building-with-testing_buildblockv1) for architectural details.
