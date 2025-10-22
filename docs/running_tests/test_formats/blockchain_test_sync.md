# Blockchain Engine Sync Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Engine Sync Test fixture format tests are included in the fixtures subdirectory `blockchain_tests_sync`, and use Engine API directives to test client synchronization capabilities after fixtures are executed with valid payloads.

These are produced by the `BlockchainTest` test spec when `pytest.mark.verify_sync` is used as a test marker.

## Description

The Blockchain Engine Sync Test fixture format is used to test execution client synchronization between peers. It validates that clients can correctly sync state and blocks from another client using the Engine API and P2P networking.

The test works by:

1. Setting up a client under test, defining a pre-execution state, a series of `engine_newPayloadVX` directives, and a post-execution state, as in Blockchain Engine Test fixture formats.
2. Starting a sync client with the same genesis and pre-execution state.
3. Having the sync client synchronize from the client under test.
4. Verifying that both clients reach the same final state.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`HiveFixture`](#hivefixture) test object, with the key string representing the test name.

The JSON file path plus the test name are used as the unique test identifier, as well as a `{client under test}::sync_{sync client}` identifier.

## Consumption

For each [`HiveFixture`](#hivefixture) test object in the JSON fixture file, perform the following steps:

### Client Under Test Setup

1. Start the client under test using:
    - [`network`](#-network-fork) to configure the execution fork schedule according to the [`Fork`](./common_types.md#fork) type definition.
    - [`pre`](#-pre-alloc) as the starting state allocation of the execution environment for the test and calculate the genesis state root.
    - [`genesisBlockHeader`](#-genesisblockheader-fixtureheader) as the genesis block header.

2. Verify the head of the chain is the genesis block, and the state root matches the one calculated on step 1, otherwise fail the test.

3. Process all [`FixtureEngineNewPayload`](#fixtureenginenewpayload) objects in [`engineNewPayloads`](#-enginenewpayloads-listfixtureenginenewpayload) to build the complete chain on the client under test.

### Sync Client Setup and Synchronization

1. Start a sync client using the same genesis configuration:
    - Use the same [`network`](#-network-fork), [`pre`](#-pre-alloc), and [`genesisBlockHeader`](#-genesisblockheader-fixtureheader).

2. Establish P2P connection between the clients:
    - Get the enode URL from the client under test
    - Use `admin_addPeer` to connect the sync client to the client under test

3. Trigger synchronization on the sync client:
    - Send the [`syncPayload`](#-syncpayload-fixtureenginenewpayload) using `engine_newPayloadVX`
    - Send `engine_forkchoiceUpdatedVX` pointing to the last block hash

4. Monitor and verify synchronization:
    - Wait for the sync client to reach the [`lastblockhash`](#-lastblockhash-hash)
    - Verify the final state root matches between both clients
    - If [`post`](#-post-alloc) is provided, verify the final state matches

## Structures

### `HiveFixture`

#### - `network`: [`Fork`](./common_types.md#fork)

##### TO BE DEPRECATED

Fork configuration for the test.

This field is going to be replaced by the value contained in `config.network`.

#### - `genesisBlockHeader`: [`FixtureHeader`](./blockchain_test.md#fixtureheader)

Genesis block header.

#### - `engineNewPayloads`: [`List`](./common_types.md#list)`[`[`FixtureEngineNewPayload`](#fixtureenginenewpayload)`]`

List of `engine_newPayloadVX` directives to be processed by the client under test to build the complete chain.

#### - `syncPayload`: [`FixtureEngineNewPayload`](#fixtureenginenewpayload)

The final payload to be sent to the sync client to trigger synchronization. This is typically an empty block built on top of the last test block.

#### - `engineFcuVersion`: [`Number`](./common_types.md#number)

Version of the `engine_forkchoiceUpdatedVX` directive to use to set the head of the chain.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Starting account allocation for the test. State root calculated from this allocation must match the one in the genesis block.

#### - `lastblockhash`: [`Hash`](./common_types.md#hash)

Hash of the last valid block that the sync client should reach after successful synchronization.

#### - `post`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Account allocation for verification after synchronization is complete.

#### - `postStateHash`: [`Optional`](./common_types.md#optional)`[`[`Hash`](./common_types.md#hash)`]`

Optional state root hash for verification after synchronization is complete. Used when full post-state is not included.

#### - `config`: [`FixtureConfig`](#fixtureconfig)

Chain configuration object to be applied to both clients running the blockchain sync test.

### `FixtureConfig`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork configuration for the test. It is guaranteed that this field contains the same value as the root field `network`.

#### - `chainId`: [`Number`](./common_types.md#number)

Chain ID configuration for the test network.

#### - `blobSchedule`: [`BlobSchedule`](./common_types.md#blobschedule-mappingforkforkblobschedule)

Optional; present from Cancun on. Maps forks to their blob schedule configurations as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840).

### `FixtureEngineNewPayload`

#### - `executionPayload`: [`FixtureExecutionPayload`](#fixtureexecutionpayload)

Execution payload.

#### - `blob_versioned_hashes`: [`Optional`](./common_types.md#optional)`[`[`List`](./common_types.md#list)`[`[`Hash`](./common_types.md#hash)`]]` `(fork: Cancun)`

List of hashes of the versioned blobs that are part of the execution payload.

#### - `parentBeaconBlockRoot`: [`Optional`](./common_types.md#optional)`[`[`Hash`](./common_types.md#hash)`]` `(fork: Cancun)`

Hash of the parent beacon block root.

#### - `validationError`: [`Optional`](./common_types.md#optional)`[`[`TransactionException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.TransactionException)` | `[`BlockException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.BlockException)`]`

For sync tests, this field should not be present as sync tests only work with valid chains. Invalid blocks cannot be synced.

#### - `version`: [`Number`](./common_types.md#number)

Version of the `engine_newPayloadVX` directive to use to deliver the payload.

### `FixtureExecutionPayload`

#### - `parentHash`: [`Hash`](./common_types.md#hash)

Hash of the parent block.

#### - `feeRecipient`: [`Address`](./common_types.md#address)

Address of the account that will receive the rewards for building the block.

#### - `stateRoot`: [`Hash`](./common_types.md#hash)

Root hash of the state trie.

#### - `receiptsRoot`: [`Hash`](./common_types.md#hash)

Root hash of the receipts trie.

#### - `logsBloom`: [`Bloom`](./common_types.md#bloom)

Bloom filter composed of the logs of all the transactions in the block.

#### - `blockNumber`: [`HexNumber`](./common_types.md#hexnumber)

Number of the block.

#### - `gasLimit`: [`HexNumber`](./common_types.md#hexnumber)

Total gas limit of the block.

#### - `gasUsed`: [`HexNumber`](./common_types.md#hexnumber)

Total gas used by all the transactions in the block.

#### - `timestamp`: [`HexNumber`](./common_types.md#hexnumber)

Timestamp of the block.

#### - `extraData`: [`Bytes`](./common_types.md#bytes)

Extra data of the block.

#### - `prevRandao`: [`Hash`](./common_types.md#hash)

PrevRandao of the block.

#### - `blockHash`: [`Hash`](./common_types.md#hash)

Hash of the block.

#### - `transactions`: [`List`](./common_types.md#list)`[`[`Bytes`](./common_types.md#bytes)`]`

List of transactions in the block, in serialized format.

#### - `withdrawals`: [`List`](./common_types.md#list)`[`[`FixtureWithdrawal`](#fixturewithdrawal)`]`

List of withdrawals in the block.

#### - `baseFeePerGas`: [`HexNumber`](./common_types.md#hexnumber) `(fork: London)`

Base fee per gas of the block.

#### - `blobGasUsed`: [`HexNumber`](./common_types.md#hexnumber) `(fork: Cancun)`

Total blob gas used by all the transactions in the block.

#### - `excessBlobGas`: [`HexNumber`](./common_types.md#hexnumber) `(fork: Cancun)`

Excess blob gas of the block used to calculate the blob fee per gas for this block.

### `FixtureWithdrawal`

#### - `index`: [`HexNumber`](./common_types.md#hexnumber)

Index of the withdrawal

#### - `validatorIndex`: [`HexNumber`](./common_types.md#hexnumber)

Withdrawing validator index

#### - `address`: [`Address`](./common_types.md#address)

Address to withdraw to

#### - `amount`: [`HexNumber`](./common_types.md#hexnumber)

Amount of the withdrawal

## Differences from Blockchain Engine Tests

While the Blockchain Sync Test format is similar to the Blockchain Engine Test format, there are key differences:

1. **`syncPayload` field**: Contains the final block used to trigger synchronization on the sync client.
2. **Multi-client testing**: Tests involve two clients (client under test and sync client) rather than a single client.
3. **P2P networking**: Tests require P2P connection establishment between clients.
4. **No invalid blocks**: Sync tests only work with valid chains as invalid blocks cannot be synced.
5. **`postStateHash` field**: Optional field for state verification when full post-state is not included.

## Fork Support

Blockchain Sync Tests are only supported for post-merge forks (Paris and later) as they rely on the Engine API for synchronization triggering.
