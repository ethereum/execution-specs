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
| [`consume enginex`](#enginex)           | Client imports blocks via Engine API in Hive, optimized by client reuse            | EVM, block processing, Engine API, chain reorgs (implicit\*\*) | Staging, Hive | System test                       |
| [`consume sync`](#sync)                 | Client syncs from another client using Engine API in Hive                               | EVM, block processing, Engine API, P2P sync                  | Staging, Hive | System test                       |
| [`consume wirex`](#wirex)               | Client full syncs fixture blocks from a mock devp2p peer in Hive, with client reuse     | EVM, block processing, Engine API (sync trigger), devp2p     | Staging, Hive | System test                       |
| [`consume rlp`](#rlp)                   | Client imports RLP-encoded blocks upon start-up in Hive                                 | EVM, block processing, RLP import (sync\*)                   | Staging, Hive | System test                       |
| [`build-block`](#block-building)        | Client builds blocks via `testing_buildBlockV1` in Hive, validated against fixture       | EVM, block production, Engine API (testing namespace)        | Staging, Hive | System test                       |
| [`execute hive`](./execute/hive.md)     | Tests executed against a client via JSON RPC `eth_sendRawTransaction` in Hive           | EVM, JSON RPC, mempool                                       | Staging, Hive | System test                       |
| [`execute remote`](./execute/remote.md) | Tests executed against a client via JSON RPC `eth_sendRawTransaction` on a live network | EVM, JSON RPC, mempool, EL-EL/EL-CL interaction (indirectly) | Production    | System Test                       |

\*sync: Depending on code paths used in the client implementation, see the [RLP vs Engine Simulator section below](#engine-vs-rlp-simulator).

\*\*chain reorgs: A side-effect of client reuse, not something the test cases describe, see the [Implicit Chain Reorg Coverage section below](#implicit-chain-reorg-coverage).

The following sections describe the different methods in more detail.

!!! note "`./hive --sim=eels/consume-engine` vs `consume engine`"

     The execution-specs simulators can be ran either standalone using the `./hive` command or via a `uv`/Python-based command against a `./hive --dev` backend, more details are [provided below](#two-methods-to-run-eels-simulators).

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
| Simulator      | `eels/consume-engine`    |
| Fixture format | `blockchain_test_engine` |

The consume engine method tests execution clients via the Engine API by sending block payloads and verifying the response (post-merge forks only). This method provides the most realistic testing environment for production Ethereum client behavior, covering consensus integration, payload validation, and state synchronization.

The `consume engine` command:

1. **Initializes the execution client** with genesis state.
2. **Connects via Engine API** (port 8551), primitively mocking a consensus client.
3. **Sends a forkchoice update** to the genesis block to establish the chain head.
4. **Verifies the client's genesis block hash** via `eth_getBlockByNumber(0)`.
5. **Submits payloads** using `engine_newPayload` calls.
6. **Validates responses** against expected results.
7. **Sends a forkchoice update** after each valid payload to advance the chain head.
8. **Tests error conditions** and exception handling.

## EngineX

| Nomenclature   |                            |
| -------------- | -------------------------- |
| Command        | `consume enginex`          |
| Simulator      | `eels/consume-enginex`     |
| Fixture format | `blockchain_test_engine_x` |

The EngineX method is a faster alternative to `consume engine` that executes multiple tests against a single client instance. This is achieved via the [Blockchain Engine X Test fixture format](./test_formats/blockchain_test_engine_x.md) which groups tests that share the same fork and EVM [Environment](./test_formats/state_test.md#fixtureenvironment) together and contains a larger, shared pre-allocation state that all tests in the group use. This allows the EngineX simulator to execute multiple tests against the same client instance, whereas the Engine Simulator starts a fresh client for each test.

The `consume enginex` command, for each pre-allocation group:

1. **Initializes the execution client** with the group's shared genesis state.
2. **Connects via Engine API** (port 8551).
3. **Executes all tests in the group** against the same client. Each test:

    - Sends a forkchoice update to the genesis block, resetting the chain head.
    - Verifies the client's genesis block hash via `eth_getBlockByNumber(0)`; this is only done for the first test executed against the client, as genesis is immutable.
    - Submits payloads from the test using `engine_newPayload` calls.
    - Validates responses against expected results.
    - Sends a forkchoice update after each valid payload to advance the chain head.
    - Tests error conditions and exception handling.

4. **Stops the client** when all tests in the group complete.

### Implicit Chain Reorg Coverage

Client reuse gives `consume enginex` coverage that `consume engine` does not have. The forkchoice update at the start of each test resets the client's head from the previous test's chain tip back to genesis. The payload that follows is therefore a sibling of a block the client already imported and considered canonical (the same parent and block number, but a different block hash), and the forkchoice update sent after it makes the new branch canonical.

Every test after the first in a pre-allocation group consequently exercises the client's chain reorganization path: rolling the head state back to an ancestor, importing a competing block at an already-occupied height, and re-canonicalizing a new branch.

!!! note "This coverage is implicit"

    No `blockchain_test_engine_x` fixture describes a reorg; the reorgs are an artifact of how the simulator reuses clients. A test whose payloads are all invalid also leaves the head at genesis, so no rollback precedes the next test in the group.

    It does mean, however, that a test which fails under `consume enginex` but passes under `consume engine` is more likely to indicate a bug in the client's reorg, head state rollback or block caching logic than in its EVM or block validation logic.

### Bad-Block Cache Handling

Clients typically cache the blocks they reject. Because a client is reused across a pre-allocation group, its bad-block cache persists between tests: if two tests in a group contain an identical invalid block, the client validates the first submission for real and returns the specific validation error, but may answer the resubmission from its cache with a generic error (e.g. geth's and reth's "links to previously rejected block" or Nethermind's "is known to be a part of an invalid chain") that maps to no known exception.

The simulator therefore remembers the first validation error each client returns per invalid block. When a rejection does not match the test's expected exception, it is verified against the client's first rejection of the same block: it is accepted and logged ("Accepting mismatched validation error") if that first rejection matched the expected exception, and fails the test as before otherwise. This is sound because an identical block hash implies an identical block built on an identical parent chain, so the real validation outcome is deterministic. `consume engine` starts a fresh client per test and is unaffected.

### Engine vs EngineX

|                         | `consume engine`                                                     | `consume enginex`                                                                          |
| ----------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Fixture format**      | [`blockchain_test_engine`](./test_formats/blockchain_test_engine.md) | [`blockchain_test_engine_x`](./test_formats/blockchain_test_engine_x.md)                       |
| **Client lifecycle**    | New client per test                                                  | Client reused across tests with same pre-alloc                                                 |
| **Engine API flow**     | FCU to genesis, then an `engine_newPayload` and FCU per valid payload | Identical, to keep both methods equivalent                                                    |
| **Genesis block check** | `eth_getBlockByNumber(0)` per test                                    | `eth_getBlockByNumber(0)` once per client; genesis is immutable                                |
| **Execution speed**     | Slower (client startup overhead)                                     | Faster (amortized startup cost)                                                                |
| **Test isolation**      | Full isolation                                                       | Shared client and genesis state within group; the chain head is reset to genesis for each test |
| **Chain reorgs**        | Not exercised; each client executes one test's payloads only         | [Implicitly exercised](#implicit-chain-reorg-coverage) by every test after the first in a group |
| **Exception matching**  | Response validated directly against the expected exception           | Identical, except a mismatched rejection is [accepted](#bad-block-cache-handling) if the client's first rejection of the identical block matched |

EngineX achieves faster execution by:

1. **Grouping tests** by their pre-allocation state (genesis configuration).
2. **Reusing clients** across all tests in a group, avoiding repeated client startup.
3. **Skipping the redundant genesis block check** for reused clients: the client's genesis block hash is verified once per client, instead of once per test.

!!! note "When to use EngineX vs Engine"

    Use `consume enginex` for faster test runs when full per-test isolation is not required. Use `consume engine` when you need complete isolation between tests or when debugging issues triggered by a single test case.

## RLP

| Nomenclature   |                    |
| -------------- | ------------------ |
| Command        | `consume rlp`      |
| Simulator      | `eels/consume-rlp` |
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

## WireX

| Nomenclature   |                            |
| -------------- | -------------------------- |
| Command        | `consume wirex`            |
| Simulator      | `eels/consume-wirex`       |
| Fixture format | `blockchain_test_engine_x` |

The WireX method makes the client under test full sync each test's chain from a deterministic mock devp2p peer implemented inside the testing framework. The intent is to verify that clients can receive and propagate blocks over devp2p using the consensus test corpus; it is not intended to be a complete test of historical sync. WireX intends to replace `consume rlp` for post-Merge forks: the same workload moves from a client-specific offline import onto the client's production peer-to-peer block ingestion path, and EngineX-style client reuse amortizes the client startup cost that dominates `consume rlp` runs.

The `consume wirex` command, for each pre-allocation group:

1. **Initializes the execution client** with the group's shared genesis state.
2. **Connects a mock devp2p peer** to the client (RLPx and eth handshakes).
3. **Executes each fixture's resolved sync paths.** For each path, WireX:

    - Reconstructs the root-to-leaf chain selected by an emitted `syncPayloads` target, or falls back to the authored chain when the fixture has no targets.
    - Uses the group's reused client for a single-target fixture and an isolated client and peer for every target of a multi-target fixture.
    - Installs the selected chain on the peer and names its target over the Engine API with `engine_newPayload` and `engine_forkchoiceUpdated`.
    - Waits while the client downloads the missing ancestry from the peer and processes it through its full-sync path.
    - Verifies the valid or rejected outcome and, where the target topology guarantees transport, asserts per block hash that the required headers and bodies were served over devp2p.

4. **Stops the client** when all tests in the group complete.

See [Consume WireX](./consume/wirex.md) for the full flow, including a process diagram, the peer's behavior, rejection tests, and command options.

## Block Building

| Nomenclature   |                          |
| -------------- | ------------------------ |
| Command        | `build-block`            |
| Simulator      | `eels/build-block`       |
| Fixture format | `blockchain_test_engine` |

The block-building method tests the **producer-side** of an execution client: rather than asking the client to validate and import a pre-built block, it asks the client to build a block from inputs (parent, payload attributes, transactions) and then validates the resulting block field-by-field against the fixture's expected block. This exercises tx ordering, gas accounting, payload assembly, and (for fork ≥ Prague) `executionRequests` derivation.

The endpoint used is `testing_buildBlockV1`, an engine-API testing-namespace method exposed by `ethpandaops/<client>:master` (and similar performance builds). It is not part of the standard Engine API — the testing namespace is opt-in and intended for fixture-driven block-building verification.

The `build-block` command, for each valid payload in the fixture:

1. **Builds the block** via `testing_buildBlockV1(parent_hash, payload_attributes, transactions, extra_data)`. The client returns its own constructed `ExecutionPayload`.
2. **Validates execution-dependent fields** of the built payload against the fixture's expected payload (everything except `gas_limit` and `block_hash`, which depend on client-side EIP-1559 elasticity and are validated via a range check separately).
3. **Validates `executionRequests`** for fork ≥ Prague (`engine_newPayloadV4+`).
4. **Imports the fixture block** (not the client-built one) via `engine_newPayloadVX` so the chain advances with the fixture's expected gas limit and block hash.
5. **Advances the chain** via `engine_forkchoiceUpdatedVX`.

This complements `consume engine`: where `consume engine` tests the client's payload-validation path, `build-block` tests its payload-production path against the same fixtures.

## Engine vs RLP Simulator

The RLP Simulator (`eels/consume-rlp`) and the Engine Simulator (`eels/consume-engine`) should be seen as complimentary to one another. Although they execute the same underlying EVM test cases, the block validation logic is executed via different client code paths (using different [fixture formats](./test_formats/index.md)). Therefore, ideally, **both simulators should be executed for full coverage**.

### Code Path Choices

Clients consume fixtures in the `eels/consume-engine` simulator via the Engine API's `EngineNewPayloadv*` endpoint; a natural way to validate, respectively invalidate, block payloads. In this case, there is no flexibility in the choice of code path - it directly harnesses mainnet client functionality. The `eels/consume-rlp` Simulator, however, allows clients more freedom, as the rlp-encoded blocks are imported upon client startup. Clients are recommended to try and hook the block import into the code path used for historical syncing.

### Differences

|                         | `eels/consume-rlp`                                    | `eels/consume-engine`                                              |
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

## Two Methods to Run EELS Simulators

Many of the methods use the Hive Testing Environment to interact with clients and run tests against them. These methods are also called Hive simulators. While Hive is always necessary to run simulators, they can be called in two different ways. Both of these commands execute the same simulator code, but in different environments, we take the example of the `eels/consume-engine` simulator:

1. `./hive --sim=eels/consume-engine` is a standalone command that installs and configures execution-specs and its `consume` command in a dockerized container managed by Hive. This is the standard method to execute EEST [fixture releases](./releases.md) against clients in CI environments and is the method to generate the results at [hive.ethpandaops.io](https://hive.ethpandaops.io). See [Hive](./hive/index.md) and its [Common Options](./hive/common_options.md) for help with this method.
2. `uv run consume engine` requires the user to clone and [configure execution-specs](../getting_started/installation.md) and start a Hive server in [development mode](./hive/dev_mode.md). In this case, the simulator runs on the native system and communicate to the client via the Hive API. This is particularly useful during test development as fixtures on the local disk can be specified via `--input=fixtures/`. As the simulator runs natively, it is easy to drop into a debugger and inspect the simulator or client container state. See [Hive Developer Mode](./hive/dev_mode.md) for help with this method.
