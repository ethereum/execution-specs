# Blockchain Engine Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Engine Test fixture format tests are included in the fixtures subdirectory `blockchain_tests_engine`, and use Engine API directives instead of the usual BlockchainTest format.

These are produced by the `StateTest` and `BlockchainTest` test specs.

## Description

The Blockchain Engine Test fixture format is used to test block validation and the consensus rules of the Ethereum blockchain, when a block is delivered through the Engine API as a `engine_newPayloadVX` directive.

It does so by defining a pre-execution state, a series of blocks as `engine_newPayloadVX` directives, and a post-execution state, verifying that, after all the blocks have been processed, appended if valid or rejected if invalid, the result is the expected post-execution state.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`HiveFixture`](#hivefixture) test object, with the key string representing the test name.

The JSON file path plus the test name are used as the unique test identifier.

## Consumption

For each [`HiveFixture`](#hivefixture) test object in the JSON fixture file, perform the following steps:

1. Start a full node using:

    - [`network`](#-network-fork) to configure the execution fork schedule according to the [`Fork`](./common_types.md#fork) type definition.
    - [`pre`](#-pre-alloc) as the starting state allocation of the execution environment for the test and calculate the genesis state root.
    - [`genesisBlockHeader`](#-genesisblockheader-fixtureheader) as the genesis block header.

2. Verify the head of the chain is the genesis block, and the state root matches the one calculated on step 1, otherwise fail the test.

3. For each [`FixtureEngineNewPayload`](#fixtureenginenewpayload) in [`engineNewPayloads`](#-enginenewpayloads-listfixtureenginenewpayload):

    1. Deliver the payload using the `engine_newPayloadVX` directive, using:
        - [`version`](#-version-number) as the version of the directive.
        - [`executionPayload`](#-executionpayload-fixtureexecutionpayload) as the payload.
        - [`blob_versioned_hashes`](#-blob_versioned_hashes-optionallisthash-fork-cancun), if present, as the list of hashes of the versioned blobs that are part of the execution payload.
        - [`parentBeaconBlockRoot`](#-parentbeaconblockroot-optionalhash-fork-cancun), if present, as the hash of the parent beacon block root.
    2. If [`errorCode`](#-errorcode-optionalnumber) is present:
        - Verify the directive returns an error, and the error code matches the one in [`errorCode`](#-errorcode-optionalnumber), otherwise fail the test.
        - Proceed to the next payload.
    3. If `valid` is `false`, verify that the directive returns `status` field of [PayloadStatusV1](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#payloadstatusv1) as `INVALID`, otherwise fail the test.
    4. If `valid` is `true`, verify that the directive returns `status` field of [PayloadStatusV1](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#payloadstatusv1) as `VALID`, otherwise fail the test.

## Structures

### `HiveFixture`

#### - `network`: [`Fork`](./common_types.md#fork)

##### TO BE DEPRECATED

Fork configuration for the test.

This field is going to be replaced by the value contained in `config.network`.

#### - `genesisBlockHeader`: [`FixtureHeader`](./blockchain_test.md#fixtureheader)

Genesis block header.

#### - `engineNewPayloads`: [`List`](./common_types.md#list)`[`[`FixtureEngineNewPayload`](#fixtureenginenewpayload)`]`

List of `engine_newPayloadVX` directives to be processed after the genesis block.

#### - `engineFcuVersion`: [`Number`](./common_types.md#number)

Version of the `engine_forkchoiceUpdatedVX` directive to use to set the head of the chain.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Starting account allocation for the test. State root calculated from this allocation must match the one in the genesis block.

#### - `lastblockhash`: [`Hash`](./common_types.md#hash)

Hash of the last valid block, or the genesis block hash if the list of blocks is empty, or contains a single invalid block.

#### - `post`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Account allocation for verification after all the blocks have been processed.

#### - `config`: [`FixtureConfig`](#fixtureconfig)

Chain configuration object to be applied to the client running the blockchain engine test.

### `FixtureConfig`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork configuration for the test. It is guaranteed that this field contains the same value as the root field `network`.

#### - `blobSchedule`: [`BlobSchedule`](./common_types.md#blobschedule-mappingforkforkblobschedule)

Optional; present from Cancun on. Maps forks to their blob schedule configurations as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840).

### `FixtureEngineNewPayload`

#### - `executionPayload`: [`FixtureExecutionPayload`](#fixtureexecutionpayload)

Execution payload.

#### - `blob_versioned_hashes`: [`Optional`](./common_types.md#optional)`[`[`List`](./common_types.md#list)`[`[`Hash`](./common_types.md#hash)`]]` `(fork: Cancun)`

List of hashes of the versioned blobs that are part of the execution payload.
They can mismatch the hashes of the versioned blobs in the execution payload, for negative-testing reasons.

#### - `parentBeaconBlockRoot`: [`Optional`](./common_types.md#optional)`[`[`Hash`](./common_types.md#hash)`]` `(fork: Cancun)`

Hash of the parent beacon block root.

#### - `validationError`: [`TransactionException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.TransactionException)` | `[`BlockException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.BlockException)

Validation error expected when executing the payload.

When the payload is valid, this field is not present, and a `VALID` status is
expected in the `status` field of
[PayloadStatusV1](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#payloadstatusv1).

If this field is present, the `status` field of
[PayloadStatusV1](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#payloadstatusv1)
is expected to be `INVALID`.

#### - `version`: [`Number`](./common_types.md#number)

Version of the `engine_newPayloadVX` directive to use to deliver the payload.

#### - `errorCode`: [`Optional`](./common_types.md#optional)`[`[`Number`](./common_types.md#number)`]`

Error code to be returned by the `engine_newPayloadVX` directive.

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
