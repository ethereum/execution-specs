# Running Test on a Live Remote Network

Tests can be executed on a live remote network by running the `execute remote` command.

The command requires the `--fork` flag which must match the fork that is currently active in the network (fork transition tests are not supported yet).

The `execute remote` command requires to be pointed to an RPC endpoint of a client that is connected to the network, which can be specified by using the `--rpc-endpoint` flag:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io
```

Another requirement is that the command is provided with a seed account that has funds available in the network to deploy contracts and fund accounts. This can be done by setting the `--rpc-seed-key` flag:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
```

The value needs to be a private key that is used to sign the transactions that deploy the contracts and fund the accounts.

One last requirement is that the `--rpc-chain-id` flag is set to the chain id of the network that is being tested:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345
```

## Engine RPC Endpoint (Optional)

By default, the `execute remote` command assumes that the execution client is connected to a beacon node and the chain progresses automatically. However, you can optionally specify an Engine RPC endpoint to drive the chain manually when new transactions are submitted.

To use this feature, you need to provide both the `--engine-endpoint` and JWT authentication:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 --engine-endpoint=https://engine.endpoint.io --engine-jwt-secret "your-jwt-secret-here"
```

Alternatively, you can provide the JWT secret from a file:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 --engine-endpoint=https://engine.endpoint.io --engine-jwt-secret-file /path/to/jwt-secret.txt
```

The JWT secret file must contain only the JWT secret as a hex string.

When an engine endpoint is provided, the test execution will use the Engine API to create new blocks and include transactions, giving you full control over the chain progression.

The `execute remote` command will connect to the client via the RPC endpoint and will start executing every test in the `./tests` folder in the same way as the `execute hive` command, but instead of using the Engine API to generate blocks, it will send the transactions to the client via the RPC endpoint.

It is recommended to only run a subset of the tests when executing on a live network. To do so, a path to a specific test can be provided to the command:

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 ./tests/prague/eip7702_set_code_tx/test_set_code_txs.py::test_set_code_to_sstore
```

## Address Stubs for Pre-deployed Contracts

When running tests on networks that already have specific contracts deployed (such as mainnet or testnets with pre-deployed contracts), you can use the `--address-stubs` flag to specify these contracts instead of deploying new ones.

Address stubs allow you to map contract labels used in tests to actual addresses where those contracts are already deployed on the network. This is particularly useful for:

- Testing against mainnet with existing contracts (e.g., Uniswap, Compound)
- Using pre-deployed contracts on testnets
- Testing on bloat-net, a network containing pre-existing contracts with extensive storage history
- Avoiding redeployment of large contracts to save gas and time

### Using Address Stubs

You can provide address stubs in several formats:

**JSON string:**

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 --address-stubs '{"DEPOSIT_CONTRACT": "0x00000000219ab540356cbb839cbe05303d7705fa", "UNISWAP_V3_FACTORY": "0x1F98431c8aD98523631AE4a59f267346ea31F984"}'
```

**JSON file:**

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 --address-stubs ./contracts.json
```

**YAML file:**

```bash
uv run execute remote --fork=Prague --rpc-endpoint=https://rpc.endpoint.io --rpc-seed-key 0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f --rpc-chain-id 12345 --address-stubs ./contracts.yaml
```

### Address Stubs File Format

**JSON format (contracts.json):**

```json
{
  "DEPOSIT_CONTRACT": "0x00000000219ab540356cbb839cbe05303d7705fa",
  "UNISWAP_V3_FACTORY": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
  "COMPOUND_COMPTROLLER": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"
}
```

**YAML format (contracts.yaml):**

```yaml
DEPOSIT_CONTRACT: 0x00000000219ab540356cbb839cbe05303d7705fa
UNISWAP_V3_FACTORY: 0x1F98431c8aD98523631AE4a59f267346ea31F984
COMPOUND_COMPTROLLER: 0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B
```

### How Address Stubs Work

When a test deploys a contract using `pre.deploy_contract(..., stub="NAME")` and the stub name matches a key in the address stubs, the test framework will:

1. Use the pre-deployed contract at the specified address instead of deploying a new contract
2. Skip the contract deployment transaction, saving gas and time
3. Use the existing contract's code and state for the test

This is particularly useful when testing interactions with well-known contracts that are expensive to deploy or when you want to test against the actual deployed versions of contracts.

If the address is _not_ present in the stubbed addresses list, the test will fail to execute.

If the address contained in the stubbed addresses list does not contain code on the remote chain, the test will fail.

The pre-alloc will be populated with live information from the chain, so the following lines will result in up-to-date information:

```python
my_stubbed_contract = pre.deploy_contract(code, stub="uniswap")
pre[my_stubbed_contract].nonce  # Actual nonce of the contract on chain
pre[my_stubbed_contract].balance  # Actual balance of the contract on chain
```

### Bloat-net Testing

Address stubs are especially valuable when testing on **bloat-net**, a specialized network that contains pre-existing contracts with extensive storage history. On bloat-net:

- Contracts have been deployed and used extensively, accumulating large amounts of storage data
- The storage state represents real-world usage patterns with complex data structures
- Redeploying these contracts would lose the valuable historical state and storage bloat

Using address stubs on bloat-net allows you to:

- Test against contracts with realistic storage bloat patterns
- Preserve the complex state that has been built up over time
- Avoid the computational and storage costs of recreating this state
- Test edge cases that only emerge with large, real-world storage datasets

## Transaction Metadata on Remote Networks

When executing tests on remote networks, all transactions include metadata that helps with debugging and monitoring. This metadata is embedded in the RPC request ID and includes:

- **Test identification**: Each transaction is tagged with the specific test being executed
- **Execution phase**: Transactions are categorized as setup, testing, or cleanup
- **Action tracking**: Specific actions like contract deployment, funding, or refunding are tracked
- **Target identification**: The account or contract being targeted is labeled

This metadata is particularly useful when debugging test failures on live networks, as it allows you to correlate blockchain transactions with specific test operations and phases.

See [Transaction Metadata](./transaction_metadata.md) for details.

## `execute` Command Test Execution

The `execute remote` and `execute hive` commands first creates a random sender account from which all required test accounts will be deployed and funded, and this account is funded by sweeping (by default) this "seed" account.

The sweep amount can be configured by setting the `--seed-account-sweep-amount` flag:

```bash
--seed-account-sweep-amount "1000 ether"
```

Once the sender account is funded, the command will start executing tests one by one by sending the transactions from this account to the network.

Test transactions are not sent from the main sender account though, they are sent from a different unique account that is created for each test (accounts returned by `pre.fund_eoa`).

### Use with Parallel Execution

If the `execute` is run using the `-n=N` flag (respectively `--sim-parallelism=N`), n>1, the tests will be executed in parallel, and each process will have its own separate sender account, so the amount that is swept from the seed account is divided by the number of processes, and this has to be taken into account when setting the sweep amount and also when funding the seed account.

After finishing each test the command will check the remaining balance of all accounts and will attempt to recover the funds back to the sender account, and at the end of all tests, the remaining balance of the sender account will be swept back to the seed account.

There are instances where it will be impossible to recover the funds back from a test, for example, funds that are sent to a contract that has no built-in way to send them back, the funds will be stuck in the contract and they will not be recoverable.
