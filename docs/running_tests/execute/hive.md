# Executing Tests on a Hive Local Network

Execute tests run on a local network whose clients are managed by Hive. Choose the path that fits your task:

- **Run the blob simulator or reproduce a dashboard failure:** use the [published `execute-blobs` image](#the-eelsexecute-blobs-simulator) with `./hive --sim`. Hive runs the simulator and client in containers.
- **Edit tests or debug interactively:** use [development mode](#running-execute-tests-with-hive-in-dev-mode) with `./hive --dev`, then run `uv run execute hive` from your local checkout.

## The `eels/execute-blobs` Simulator

The `blob_transaction_test` execute test spec sends blob transactions to a running client. Blob transactions are fully supported in execute mode:

- Blob transactions can be sent via `eth_sendRawTransaction`
- Blob validation via `engine_getBlobsVX` endpoints (when Engine RPC available)
- Automatic gas pricing is used for the blob gas fees

Tests can be run using:

```bash
./hive --sim execute-blobs --client besu \
    --client-file ./configs/osaka.yaml
```

**Note**: If the Engine RPC is unavailable, blob transactions will be sent and `getBlobsV*` validation is skipped.

The default `execute-blobs` Dockerfile uses a published simulator image. Its tag selects the release's Python test sources; images for the branch's current release receive framework updates. See [Simulator Images](../hive/images/index.md) for setup and [Choose a tag](../hive/images/index.md#choose-a-tag) for release, devnet and nightly options. Hive accepts the short name `--sim execute-blobs`.

To select a published release explicitly:

```bash
./hive --sim execute-blobs --client go-ethereum \
    --sim.buildarg tag=v20.0.2
```

To reproduce a dashboard failure, match its simulator image, client version and configuration, and test selection. For [exact reproduction](../hive/images/how_to.md#reproduce-a-run-exactly), pin the image digest; the default `latest` image may have changed since the dashboard run. A [source build](../hive/images/how_to.md#build-from-source-with-dockerfilegit) runs both tests and framework from the selected branch; it does not select a separate release test snapshot.

See [Hive](../hive/index.md) for help installing and configuring Hive.

## Running `execute` tests with Hive in Dev Mode

Switch to development mode when you need to edit tests or simulator code, rerun quickly, or use a Python debugger. Both tests and framework now come from your checkout, rather than the release selected by a published image tag. Install the [testing tools](../../getting_started/installation.md) first; see [Hive development mode](../hive/dev_mode.md) for platform-specific setup.

Start Hive from its checkout and leave it running:

```bash
./hive --dev --client go-ethereum
```

This will start hive in dev mode with the single go-ethereum client available for launching tests.

In another terminal, from your execution-specs checkout, set the `HIVE_SIMULATOR` environment variable:

```bash
export HIVE_SIMULATOR=http://127.0.0.1:3000
```

and running:

```bash
uv run execute hive --fork=Cancun
```

Add `-k test_name` to select a test and `--pdb` to enter the debugger on failure; see [Useful Pytest Options](../useful_pytest_options.md).

If the command above leads to errors such as `ImportError: Error importing plugin "pytest_plugins.execute.rpc.hive": No module named 'hive.client'` run the following to fix it: `uv run eest clean --all`.

This will execute all available tests in the `tests` directory on the `Cancun` fork by connecting to the hive server running on `http://127.0.0.1:3000` and launching a single client with the appropriate genesis file.

The genesis file is passed to the client with the appropriate configuration for the fork schedule, system contracts and pre-allocated seed account.

All tests will be executed in the same network, in the same client, and serially, but when the `-n auto` parameter is passed to the command, the tests can also be executed in parallel.

One important feature of the `execute hive` command is that, since there is no consensus client running in the network, the command drives the chain by the use of the Engine API to prompt the execution client to generate new blocks and include the transactions in them.

## Using `testing_buildBlockV1`

Clients that implement the `testing_buildBlockV1` endpoint can use it as an alternative to the standard Engine API block building flow. Instead of sending transactions to the mempool and building blocks through `engine_forkchoiceUpdatedVX` / `engine_getPayloadVX`, the plugin sends transactions directly inside the `testing_buildBlockV1` call, which builds a block containing exactly those transactions.

With Hive running in development mode and `HIVE_SIMULATOR` set as above, pass the `--use-testing-build-block` flag:

```bash
uv run execute hive --fork=Prague --use-testing-build-block
```

This is useful when:

- The client supports the endpoint and you want faster block building (the `--get-payload-wait-time` delay is skipped).
- You want deterministic transaction ordering in each block (transactions are included in the exact order provided).

See [Block Building with `testing_buildBlockV1`](./index.md#block-building-with-testing_buildblockv1) for architectural details.
