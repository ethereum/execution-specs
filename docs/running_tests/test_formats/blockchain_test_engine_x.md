# Blockchain Engine X Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Engine X Test fixture format tests are included in the fixtures subdirectory `blockchain_tests_engine_x`, and use Engine API directives with optimized pre-allocation groups for improved execution performance.

These are produced by the `StateTest` and `BlockchainTest` test specs when using the `--generate-pre-alloc-groups` and `--use-pre-alloc-groups` flags, or by using the `--generate-all-formats` flag which generates all fixture formats including `BlockchainEngineXFixture` in a single command.

## Description

The Blockchain Engine X Test fixture format is an optimized variant of the [Blockchain Engine Test](./blockchain_test_engine.md) format designed for large-scale test execution with performance optimizations.

It uses the Engine API to test block validation and consensus rules while leveraging **pre-allocation groups** to significantly reduce test execution time and resource usage. Tests are grouped by their initial state (fork + environment + pre-allocation). Each group is executed against the same client instance using a common genesis state.

The key optimization is that **clients need only be started once per group** instead of once per test (as in the original engine fixture format), dramatically improving execution performance for large test suites.

Instead of including large pre-allocation state in each test fixture, this format references a pre-allocation groups folder (`pre_alloc`) which contains all different pre-allocation combinations organized by group.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`BlockchainTestEngineXFixture`](#blockchaintestenginexfixture) test object, with the key string representing the test name.

The JSON file path plus the test name are used as the unique test identifier.

## Pre-Allocation Groups Folder

The `blockchain_tests_engine_x` directory contains a special directory `pre_alloc` that stores pre-allocation group files used by all tests in this format, one per pre-allocation group with the name of the pre-alloc hash. This folder is essential for test execution and must be present alongside the test fixtures.

### Pre-Allocation Group File Structure

Each file in the `pre_alloc` folder corresponds to a pre-allocation group identified by a hash:

```json
{
   "testCount": 88,
   "preAccountCount": 174,
   "testIds": ["test1", "test2", ...],
   "network": "Prague",
   "chainId": "0x01",
   "groupHash": "0xb664b0d847df2cf7",
   "genesis": { ... },
   "pre": { ... }
}
```

#### Pre-Allocation Group Fields

- **`testCount`**: Number of tests in this pre-allocation group
- **`preAccountCount`**: Number of accounts in the pre-allocation group
- **`testIds`**: Array of test identifiers that belong to this group
- **`network`**: Fork name (e.g., "Prague", "Cancun")
- **`chainId`**: Chain id the group's genesis is configured for
- **`groupHash`**: The group's own hash; matches the file name and the [`preHash`](#-prehash-string) of every test in the group
- **`groupSalt`**: Optional isolation salt; only present for groups that were explicitly isolated
- **`genesis`**: Genesis block header ([`FixtureHeader`](./blockchain_test.md#fixtureheader)) shared by every test in the group, derived from the environment the group was keyed on; its state root matches the state root of `pre`
- **`pre`**: Pre-allocation group [`Alloc`](./common_types.md#alloc-mappingaddressaccount) object containing initial account states

## Consumption

For each [`BlockchainTestEngineXFixture`](#blockchaintestenginexfixture) test object in the JSON fixture file, first perform this common setup:

1. **Load Pre-Allocation Group**:
   - Read the appropriate file from the `pre_alloc` folder in the same directory
   - Locate the pre-allocation group using [`preHash`](#-prehash-string)
   - Extract the `pre` allocation and `genesis` header from the group

2. **Initialize Client**:
   - Use [`network`](#-network-fork) to configure the execution fork schedule
   - Use the pre-allocation group's `pre` allocation as the starting state
   - Use the pre-allocation group's `genesis` as the genesis block header

After setup, consume the fixture through either the Engine API or devp2p full-sync path.

### Engine API

1. For each [`FixtureEngineNewPayload`](#fixtureenginenewpayload) in [`engineNewPayloads`](#-enginenewpayloads-listfixtureenginenewpayload):
   1. Deliver the payload using `engine_newPayloadVX`.
   2. Validate the response according to the payload's expected status.
2. Ignore [`syncPayloads`](#-syncpayloads-optionallistfixtureenginenewpayload) if present. They are not Engine API directives from the test.
3. Compare the final chain head against [`lastblockhash`](#-lastblockhash-hash).
4. Verify the final state: apply [`postStateDiff`](#-poststatediff-alloc) to the pre-allocation group and verify that the result matches the client's final state.

### devp2p full sync

The optional [`syncPayloads`](#-syncpayloads-optionallistfixtureenginenewpayload) list lets a system-test consumer deliver the test blocks over devp2p. Chain relationships come only from hashes. Timestamps select fork context; they do not identify ancestry. [`lastblockhash`](#-lastblockhash-hash) remains the final valid test block after all Engine API directives have been processed; it does not identify expected-invalid sibling chains.

For each entry in `syncPayloads`:

1. Read the sync payload's `parentHash`, which identifies its test-chain head.
2. Look that hash up by `blockHash` in `engineNewPayloads`.
3. Follow `parentHash` links backwards until genesis.
4. Reverse that path and serve it over devp2p with the sync payload appended.
5. Announce the sync payload with `engine_newPayload` and `forkchoiceUpdated`.

The client is expected to reject a reconstructed chain if it contains a test payload with `validationError`; otherwise it is expected to sync successfully. Across all sync payloads, every representable test payload occurs in at least one chain. See [Sync Payloads](../../filling_tests/sync_payloads.md) for how the filler builds the list and when it can be absent.

## Structures

### `BlockchainTestEngineXFixture`

#### - `network`: [`Fork`](./common_types.md#fork)

##### TO BE DEPRECATED

Fork configuration for the test.

This field is going to be replaced by the value contained in `config.network`.

#### - `preHash`: `string`

Hash identifier referencing a pre-allocation group in the `pre_alloc` folder. This hash uniquely identifies the combination of fork, environment, and pre-allocation state that defines the group. It is `0x`-prefixed, 8 bytes wide, and matches both the group file's name and its `groupHash` field.

#### - `engineNewPayloads`: [`List`](./common_types.md#list)`[`[`FixtureEngineNewPayload`](#fixtureenginenewpayload)`]`

List of `engine_newPayloadVX` directives to be processed after the genesis block. These define the sequence of blocks to be executed via the Engine API.

#### - `syncPayloads`: [`Optional`](./common_types.md#optional)`[`[`List`](./common_types.md#list)`[`[`FixtureEngineNewPayload`](#fixtureenginenewpayload)`]]`

Ordered framework-built empty payloads, one above each test-chain head for which another block can be built. Each sync payload's `parentHash` identifies its chain head. A sync-based consumer follows the test payloads' `parentHash` links back to genesis, serves that chain with the sync payload appended, and announces the sync payload. Sync payloads above expected-invalid sibling chains precede the sync payload above the final valid chain.

The list is separate from the test's Engine API sequence. A sync payload above an expected-invalid test payload only triggers syncing: the client must fetch and reject the expected-invalid parent before it could execute the sync payload. Each sync payload's `extraData` contains a value derived from the test ID, giving it a test-specific `blockHash`. The field is absent when the fixture has no sync payloads; see [Sync Payloads](../../filling_tests/sync_payloads.md) for the sibling-chain and omission rules.

#### - `lastblockhash`: [`Hash`](./common_types.md#hash)

Hash of the last valid block after all payloads have been processed, or the genesis block hash if all payloads are invalid.

#### - `postStateDiff`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

State differences from the pre-allocation group after test execution. This optimization stores only the accounts that changed, were created, or were deleted during test execution, rather than the complete final state.

To reconstruct the final state:

1. Start with the pre-allocation group from the `pre_alloc` folder
2. Apply the changes in `postStateDiff`:
   - **Modified accounts**: Replace existing accounts with new values
   - **New accounts**: Add accounts not present in pre-allocation  
   - **Deleted accounts**: Remove accounts (represented as `null` values)

#### - `config`: [`FixtureConfig`](#fixtureconfig)

Chain configuration object to be applied to the client running the blockchain engine x test.

### `FixtureConfig`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork configuration for the test. It is guaranteed that this field contains the same value as the root field `network`.

#### - `blobSchedule`: [`BlobSchedule`](./common_types.md#blobschedule-mappingforkforkblobschedule)

Optional; present from Cancun on. Maps forks to their blob schedule configurations as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840).

### `FixtureEngineNewPayload`

Engine API payload structure identical to the one defined in [Blockchain Engine Tests](./blockchain_test_engine.md#fixtureenginenewpayload). Includes execution payload, versioned hashes, parent beacon block root, validation errors, version, and error codes.

## Usage Notes

- This format is generated when using:
    - `--generate-pre-alloc-groups` followed by `--use-pre-alloc-groups` (two invocations: phase 1 populates the `pre_alloc` folder, phase 2 generates only `BlockchainEngineXFixture`)
    - `--generate-all-formats` flag (automatically triggers 2-phase execution, generates all fixture formats)
- The `pre_alloc` folder is essential and must be distributed with the test fixtures
- Tests are grouped by identical (fork + environment + pre-allocation) combinations
- The format is optimized for Engine API testing (post-Paris forks)
