# Executing Tests on Local Networks or Hive

@ethereum/execution-spec-tests is capable of running tests on local networks or on Hive with a few considerations. The `execute` command runs test cases directly from the Python source (without the use of JSON fixtures).

See:

- [Execute Hive](./hive.md) for help with the `execute` simulator in order to run tests on a single-client local network.
- [Execute Remote](./remote.md) for help with executing tests on a remote network such as a devnet, or even mainnet.
- [Execute Eth Config](./eth_config.md) for help verifying client configurations on a remote network such as a devnet, or even mainnet.
- [Transaction Metadata](./transaction_metadata.md) for detailed information about transaction metadata tracking in execute mode.

The rest of this page describes how `execute` works and explains its architecture.

## The `execute` command and `pytest` plugin

The `execute` command is capable of parsing and executing all tests in the `./tests` directory, collect the transactions it requires, send them to a client connected to a network, wait for the network to include them in a block and, finally, check the resulting state of the involved smart-contracts against the expected state to validate the behavior of the clients.

It will not check for the state of the network itself, only the state of the smart-contracts, accounts and transactions involved in the tests, so it is possible that the network becomes unstable or forks during the execution of the tests, but this will not be detected by the command.

The way this is achieved is by using a pytest plugin that will collect all the tests the same way as the fill plugin does, but instead of compiling the transactions and sending them as a batch to the transition tool, they are prepared and sent to the client one by one.

Before sending the actual test transactions to the client, the plugin uses a special pre-allocation object that collects the contracts and EOAs that are used by the tests and, instead of pre-allocating them in a dictionary as the fill plugin does, it sends transactions to deploy contracts or fund the accounts for them to be available in the network.

The pre-allocation object requires a seed account with funds available in the network to be able to deploy contracts and fund accounts. In the case of a live remote network, the seed account needs to be provided via a command-line parameter, but in the case of a local hive network, the seed account is automatically created and funded by the plugin via the genesis file.

At the end of each test, the plugin will also check the remaining balance of all accounts and will attempt to automatically recover the funds back to the seed account in order to execute the following tests.

## Differences between the `fill` and `execute` plugins

The test execution with the `execute` plugin is different from the `fill` plugin in a few ways:

### EOA and Contract Addresses

The `fill` plugin will pre-allocate all the accounts and contracts that are used in the tests, so the addresses of the accounts and contracts will be known before the tests are executed, Further more, the test contracts will start from the same address on different tests, so there are collisions on the account addresses used across different tests. This is not the case with the `execute` plugin, as the accounts and contracts are deployed on the fly, from sender keys that are randomly generated and therefore are different in each execution.

Reasoning behind the random generation of the sender keys is that one can execute the same test multiple times in the same network and the plugin will not fail because the accounts and contracts are already deployed.

### Transactions Gas Price

The `fill` plugin will use a fixed and minimum gas price for all the transactions it uses for testing, but this is not possible with the `execute` plugin, as the gas price is determined by the current state of the network.

The `execute` plugin queries the network for current gas prices and defaults to 1.5x the network price to ensure transaction inclusion. Gas prices can be overridden via command-line flags (`--default-gas-price`, `--default-max-fee-per-gas`, `--default-max-priority-fee-per-gas`).

### Deferred EOA Funding

EOAs are funded after gas prices are determined, enabling accurate balance calculations based on actual network conditions. This ensures sufficient funds are allocated for all test transactions.

### Blob Transaction Support

Blob transactions are fully supported in execute mode, including automatic gas pricing for blob gas fees and validation via `engine_getBlobsVX` endpoints when the Engine RPC is available.

### Transaction Batching

When executing tests with many transactions (e.g., benchmark tests), the `execute` plugin automatically batches transactions to avoid overloading the RPC service (The experiment transaction limit for RPC is 1000 requests.). This is particularly important for large-scale tests that may generate hundreds or thousands of transactions.

**Default Behavior:**

- Transactions are sent in batches of up to 750 transactions by default
- Each batch is sent and confirmed before the next batch begins
- Progress logging shows batch number and transaction ranges

**CLI Configuration:**

The batch size can be configured via the `--max-tx-per-batch` option:

```bash
# Use smaller batches for slower RPC endpoints
execute --max-tx-per-batch 100 tests/

# Use larger batches for high-performance RPC endpoints
execute --max-tx-per-batch 1000 tests/
```

**Safety Threshold:**

A warning is logged when `max_transactions_per_batch` exceeds 1000, as this may cause RPC service instability or failures depending on the RPC endpoint's capacity.

**Use Cases:**

- **Benchmark tests**: Tests that measure gas consumption often generate many transactions
- **Stress testing**: When intentionally testing RPC endpoint limits
- **Slow RPC endpoints**: Reduce batch size to avoid timeouts on slower endpoints

### Block Building with `testing_buildBlockV1`

By default, the `execute` plugin drives block production through the Engine API: transactions are sent to the client's mempool via `eth_sendRawTransaction`, and blocks are built using the `engine_forkchoiceUpdatedVX` / `engine_getPayloadVX` / `engine_newPayloadVX` sequence.

Clients that implement the [`testing_buildBlockV1`](https://github.com/ethereum/execution-apis/blob/main/src/testing/testing_buildBlockV1.yaml) endpoint offer an alternative route that collapses transaction submission and block building into a single RPC call. When enabled, the plugin:

1. Collects the raw RLP-encoded transactions for each batch.
2. Calls `testing_buildBlockV1` with the parent block hash, payload attributes, and the transaction list.
3. Finalizes the returned payload with `engine_newPayloadVX` and `engine_forkchoiceUpdatedVX`.

Because transactions are included directly in the built block (rather than pulled from the mempool), the standard Engine API `engine_getPayloadVX` call and the `--get-payload-wait-time` delay are both skipped.

**CLI Configuration:**

```bash
# Enable the testing_buildBlockV1 route
execute hive --fork=Prague --use-testing-build-block
```

This flag is available for both `execute hive` and `execute remote` (when an engine endpoint is configured). See [Execute Hive](./hive.md) and [Execute Remote](./remote.md) for mode-specific details.
