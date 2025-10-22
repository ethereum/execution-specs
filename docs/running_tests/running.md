# Methods of Running Tests

EEST has two commands, `consume` and `execute`, that run test cases against EL clients:

1. `consume` runs JSON test fixtures against a client - the client is said to "consume" the test case fixture.
2. `execute` runs test cases from Python source against a client - the test case is "executed" against the client.

## Top-Level Comparison

Both `consume` and `execute` provide sub-commands which correspond to different methods of testing EL clients using EEST test cases:

| Command                                 | Description                                                                             | Components tested                                            | Environment   | Scope                             |
| --------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------- | --------------------------------- |
| [`consume direct`](#direct)             | Client consume tests via a `statetest` interface                                        | EVM                                                          | None          | Module test                       |
| [`consume direct`](#direct)             | Client consume tests via a `blocktest` interface                                        | EVM, block processing                                        | None          | Module test,</br>Integration test |
| [`consume engine`](#engine)             | Client imports blocks via Engine API `EngineNewPayload` in Hive                         | EVM, block processing, Engine API                            | Staging, Hive | System test                       |
| [`consume sync`](#sync)                 | Client syncs from another client using Engine API in Hive                               | EVM, block processing, Engine API, P2P sync                  | Staging, Hive | System test                       |
| [`consume rlp`](#rlp)                   | Client imports RLP-encoded blocks upon start-up in Hive                                 | EVM, block processing, RLP import (sync\*)                   | Staging, Hive | System test                       |
| [`execute hive`](./execute/hive.md)     | Tests executed against a client via JSON RPC `eth_sendRawTransaction` in Hive           | EVM, JSON RPC, mempool                                       | Staging, Hive | System test                       |
| [`execute remote`](./execute/remote.md) | Tests executed against a client via JSON RPC `eth_sendRawTransaction` on a live network | EVM, JSON RPC, mempool, EL-EL/EL-CL interaction (indirectly) | Production    | System Test                       |

\*sync: Depending on code paths used in the client implementation, see the [RLP vs Engine Simulator section below](#engine-vs-rlp-simulator).

The following sections describe the different methods in more detail.

!!! note "`./hive --sim=eest/consume-engine` vs `consume engine`"

     EEST simulators can be ran either standalone using the `./hive` command or via an EEST command against a `./hive --dev` backend, more details are [provided below](#two-methods-to-run-eest-simulators).

## Direct

| Nomenclature    |                                     |
| --------------- | ----------------------------------- |
| Command         | `consume direct`                    |
| Simulator       | `None`                              |
| Fixture Formats | `state_test`,</br>`blockchain_test` |

The direct method provides the fastest way to test EVM functionality by executing tests directly through a client's dedicated test interface (e.g. [`statetest`](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/staterunner.go) or [`blocktest`](https://github.com/ethereum/go-ethereum/blob/35dd84ce2999ecf5ca8ace50a4d1a6abc231c370/cmd/evm/blockrunner.go)). This method requires clients to implement a custom interface to read tests and pass their inputs through appropriate code paths; implementation guides available for [state tests](./test_formats/state_test.md#consumption) and [blockchain tests](./test_formats/blockchain_test.md#consumption).

The EEST `consume direct` command is a small wrapper around client direct interfaces that allows fast and easy selection of test subsets to execute via [test ID](../filling_tests/test_ids.md) regex match (thanks to [an index file](./consume/cache.md#the-fixture-index-file)). See [Consume Direct](./consume/direct.md) and the [Cache and Fixture Inputs](./consume/cache.md) and [Useful Pytest Options](./useful_pytest_options.md) pages for help with options.

!!! tip "Rapid EVM development"

    The [`direct` method](./consume/direct.md) with the [`StateTest` format](./test_formats/state_test.md) should be used for the fastest EVM development feedback loop. Additionally, EVM traces can be readily generated and compared to other implementations.

## Engine

| Nomenclature   |                          |
| -------------- | ------------------------ |
| Command        | `consume engine`         |
| Simulator      | `eest/consume-engine`    |
| Fixture format | `blockchain_test_engine` |

The consume engine method tests execution clients via the Engine API by sending block payloads and verifying the response (post-merge forks only). This method provides the most realistic testing environment for production Ethereum client behavior, covering consensus integration, payload validation, and state synchronization.

The `consume engine` command:

1. **Initializes the execution client** with genesis state.
2. **Connects via Engine API** (port 8551), primitively mocking a consensus client.
3. **Sends a forkchoice update** to establish the chain head.
4. **Submits payloads** using `engine_newPayload` calls.
5. **Validates responses** against expected results.
6. **Tests error conditions** and exception handling.

## RLP

| Nomenclature   |                    |
| -------------- | ------------------ |
| Command        | `consume rlp`      |
| Simulator      | `eest/consume-rlp` |
| Fixture format | `blockchain_test`  |

The RLP consumption method tests execution clients by providing them with RLP-encoded blocks to load upon startup, similar to the block import process during historical synchronization. This method tests the client's core block processing logic without the overhead of network protocols.

The `consume rlp` command:

1. **Reads blockchain test fixtures** from the specified input source.
2. **Extracts RLP-encoded blocks** from the fixture files.
3. **Copies blocks to the client's container** via files in the `/blocks/` directory.
4. **Starts the client** with the genesis state and block files.
5. **Validates the client's final `blockHash`** via JSON RPC against the test's expectations.

This method simulates how clients import blocks during historical sync, testing the complete block validation and state transition pipeline, see below for more details and a comparison to consumption via the Engine API.

## Sync

| Nomenclature   |                        |
| -------------- |------------------------|
| Command        | `consume sync`         |
| Simulator      | None                   |
| Fixture format | `blockchain_test_sync` |

The consume sync method tests execution client synchronization capabilities by having one client sync from another via the Engine API and P2P networking. This method validates that clients can correctly synchronize state and blocks from peers, testing both the Engine API, sync triggering, and P2P block propagation mechanisms.

The `consume sync` command:

1. **Initializes the client under test** with genesis state and executes all test payloads.
2. **Spins up a sync client** with the same genesis state.
3. **Establishes P2P connection** between the two clients, utilizing ``admin_addPeer`` with enode url.
4. **Triggers synchronization** by sending the target block to the sync client via `engine_newPayload` followed by `engine_forkchoiceUpdated` requests.
5. **Monitors sync progress** and validates that the sync client reaches the same state.
6. **Verifies final state** matches between both clients.

## Engine vs RLP Simulator

The RLP Simulator (`eest/consume-rlp`) and the Engine Simulator (`eest/consume-engine`) should be seen as complimentary to one another. Although they execute the same underlying EVM test cases, the block validation logic is executed via different client code paths (using different [fixture formats](./test_formats/index.md)). Therefore, ideally, **both simulators should be executed for full coverage**.

### Code Path Choices

Clients consume fixtures in the `eest/consume-engine` simulator via the Engine API's `EngineNewPayloadv*` endpoint; a natural way to validate, respectively invalidate, block payloads. In this case, there is no flexibility in the choice of code path - it directly harnesses mainnet client functionality. The `eest/consume-rlp` Simulator, however, allows clients more freedom, as the rlp-encoded blocks are imported upon client startup. Clients are recommended to try and hook the block import into the code path used for historical syncing.

### Differences

|                         | `eest/consume-rlp`                                    | `eest/consume-engine`                                              |
| ----------------------- | ----------------------------------------------------- | ------------------------------------------------------------------ |
| **Fixture Format Used** | [`BlockchainTest`](./test_formats/blockchain_test.md) | [`BlockchainTestEngine`](./test_formats/blockchain_test_engine.md) |
| **Fork support**        | All forks (including pre-merge)                       | Post-merge forks only (Paris+)                                     |
| **Client code path**    | Historical sync / block import pipeline               | Engine API / consensus integration                                 |
| **Real-world analogy**  | Blocks received during sync                           | Blocks received from consensus client                              |
| **Interface**           | Block import upon start-up via RLP files              | Engine API calls (`newPayload`, `forkchoiceUpdated`)               |
| **Exception testing**   | Basic exception handling                              | Advanced exception verification with client-specific mappers       |

!!! hint "Running both simulators adds some redundancy that can assist test debugging"

    If Engine tests fail but RLP tests pass, the issue is likely in your Engine API implementation rather than core EVM logic.

## Execute

See [Execute Command](./execute/index.md).

## Two Methods to Run EEST Simulators

Many of the methods use the Hive Testing Environment to interact with clients and run tests against them. These methods are also called Hive simulators. While Hive is always necessary to run simulators, they can be called in two different ways. Both of these commands execute the same simulator code, but in different environments, we take the example of the `eest/consume-engine` simulator:

1. `./hive --sim=eest/consume-engine` is a standalone command that installs EEST and the `consume` command in a dockerized container managed by Hive. This is the standard method to execute EEST [fixture releases](./releases.md) against clients in CI environments and is the method to generate the results at [hive.ethpandaops.io](https://hive.ethpandaops.io). See [Hive](./hive/index.md) and its [Common Options](./hive/common_options.md) for help with this method.
2. `uv run consume engine` requires the user to clone and [install EEST](../getting_started/installation.md) and start a Hive server in [development mode](./hive/dev_mode.md). In this case, the simulator runs on the native system and communicate to the client via the Hive API. This is particularly useful during test development as fixtures on the local disk can be specified via `--input=fixtures/`. As the simulator runs natively, it is easy to drop into a debugger and inspect the simulator or client container state. See [Hive Developer Mode](./hive/dev_mode.md) for help with this method.
