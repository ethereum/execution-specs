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

At the moment, the `execute` plugin does not query the client for the current gas price, but instead uses a fixed increment to the gas price in order to avoid the transactions to be stuck in the mempool.
