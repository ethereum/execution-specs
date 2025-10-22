# Blockchain Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Test fixture format tests are included in the fixtures subdirectory `blockchain_tests`.

These are produced by the `StateTest` and `BlockchainTest` test specs.

## Description

The blockchain test fixture format is used to test block validation and the consensus rules of the Ethereum blockchain.

It does so by defining a pre-execution state, a series of blocks, and a post-execution state, verifying that, after all the blocks have been processed, appended if valid or rejected if invalid, the result is the expected post-execution state.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`Fixture`](#fixture) test object, with the key string representing the test name.

The JSON file path plus the test name are used as the unique test identifier.

## Consumption

For each [`Fixture`](#fixture) test object in the JSON fixture file, perform the following steps:

1. Use [`network`](#-network-fork) to configure the execution fork schedule according to the [`Fork`](./common_types.md#fork) type definition.
2. Use [`pre`](#-pre-alloc) as the starting state allocation of the execution environment for the test and calculate the genesis state root.
3. Decode [`genesisRLP`](#-genesisrlp-bytes) to obtain the genesis block header, if the block cannot be decoded, fail the test.
4. Compare the genesis block header with [`genesisBlockHeader`](#-genesisblockheader-fixtureheader), if any field does not match, fail the test.
5. Compare the state root calculated on step 2 with the state root in the genesis block header, if they do not match, fail the test.
6. Set the genesis block as the current head of the chain.
7. If [`blocks`](#-blocks-listfixtureblockinvalidfixtureblock) contains at least one block, perform the following steps for each [`FixtureBlock`](#fixtureblock) or [`InvalidFixtureBlock`](#invalidfixtureblock):

    1. Determine whether the current block is valid or invalid:

        1. If the [`expectException`](#-expectexception-transactionexceptionblockexception) field is not present, it is valid, and object must be decoded as a [`FixtureBlock`](#fixtureblock).
        2. If the [`expectException`](#-expectexception-transactionexceptionblockexception) field is present, it is invalid, and object must be decoded as a [`InvalidFixtureBlock`](#invalidfixtureblock).

    2. Attempt to decode field [`rlp`](#-rlp-bytes) as the current block
        1. If the block cannot be decoded:
            - If an rlp decoding exception is not expected for the current block, fail the test.
            - If an rlp decoding error is expected, pass the test (Note: A block with an expected exception will be the last block in the fixture).
        2. If the block can be decoded, proceed to the next step.

    3. Attempt to apply the current decoded block on top of the current head of the chain
        1. If the block cannot be applied:
            - If an exception is expected on the current block and it matches the exception obtained upon execution, pass the test. (Note: A block with an expected exception will be the last block in the fixture)
            - If an exception is not expected on the current block, fail the test
        2. If the block can be applied:
            - If an exception is expected on the current block, fail the test
            - If an exception is not expected on the current block, set the decoded block as the current head of the chain and proceed to the next block until you reach the last block in the fixture.

8. Compare the hash of the current head of the chain against [`lastblockhash`](#-lastblockhash-hash), if they do not match, fail the test.
9. Compare all accounts and the fields described in [`post`](#-post-alloc) against the current state, if any do not match, fail the test.

## Structures

### `Fixture`

#### - `network`: [`Fork`](./common_types.md#fork)

##### TO BE DEPRECATED

Fork configuration for the test.

This field is going to be replaced by the value contained in `config.network`.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Starting account allocation for the test. State root calculated from this allocation must match the one in the genesis block.

#### - `genesisRLP`: [`Bytes`](./common_types.md#bytes)

RLP serialized version of the genesis block.

#### - `genesisBlockHeader`: [`FixtureHeader`](#fixtureheader)

Genesis block header.

#### - `blocks`: [`List`](./common_types.md#list)`[`[`FixtureBlock`](#fixtureblock)` | `[`InvalidFixtureBlock`](#invalidfixtureblock)`]`

List of blocks to be processed after the genesis block.

#### - `lastblockhash`: [`Hash`](./common_types.md#hash)

Hash of the last valid block, or the genesis block hash if the list of blocks is empty, or contains a single invalid block.

#### - `post`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Account allocation for verification after all the blocks have been processed.

#### - `sealEngine`: `str`

Deprecated: Seal engine used to mine the blocks.

#### - `config`: [`FixtureConfig`](#fixtureconfig)

Chain configuration object to be applied to the client running the blockchain test.

### `FixtureConfig`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork configuration for the test. It is guaranteed that this field contains the same value as the root field `network`.

#### - `blobSchedule`: [`BlobSchedule`](./common_types.md#blobschedule-mappingforkforkblobschedule)

Optional; present from Cancun on. Maps forks to their blob schedule configurations as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840).

### `FixtureHeader`

#### - `parentHash`: [`Hash`](./common_types.md#hash)

Hash of the parent block.

#### - `uncleHash`: [`Hash`](./common_types.md#hash)

Hash of the uncle block list.

#### - `coinbase`: [`Address`](./common_types.md#address)

Address of the account that will receive the rewards for building the block.

#### - `stateRoot`: [`Hash`](./common_types.md#hash)

Root hash of the state trie.

#### - `transactionsTrie`: [`Hash`](./common_types.md#hash)

Root hash of the transactions trie.

#### - `receiptTrie`: [`Hash`](./common_types.md#hash)

Root hash of the receipts trie.

#### - `bloom`: [`Bloom`](./common_types.md#bloom)

Bloom filter composed of the logs of all the transactions in the block.

#### - `difficulty`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Difficulty of the block.

#### - `number`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Number of the block.

#### - `gasLimit`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Total gas limit of the block.

#### - `gasUsed`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Total gas used by all the transactions in the block.

#### - `timestamp`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Timestamp of the block.

#### - `extraData`: [`Bytes`](./common_types.md#bytes)

Extra data of the block.

#### - `mixHash`: [`Hash`](./common_types.md#hash)

Mix hash or PrevRandao of the block.

#### - `nonce`: [`HeaderNonce`](./common_types.md#headernonce)

Nonce of the block.

#### - `hash`: [`Hash`](./common_types.md#hash)

Hash of the block.

#### - `baseFeePerGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: London)`

Base fee per gas of the block.

#### - `withdrawalsRoot`: [`Hash`](./common_types.md#hash) `(fork: Shanghai)`

Root hash of the withdrawals trie.

#### - `blobGasUsed`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

Total blob gas used by all the transactions in the block.

#### - `excessBlobGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

Excess blob gas of the block used to calculate the blob fee per gas for this block.

#### - `parentBeaconBlockRoot`: [`Hash`](./common_types.md#hash) `(fork: Cancun)`

Root hash of the parent beacon block.

### `FixtureBlock`

#### - `rlp`: [`Bytes`](./common_types.md#bytes)

RLP serialized version of the block. Field is only optional when embedded in a [`InvalidFixtureBlock`](#invalidfixtureblock) as the [`rlp_decoded`](#-rlp_decoded-optionalfixtureblock) field.

#### - `blockHeader`: [`FixtureHeader`](#fixtureheader)

Decoded block header fields included in the block RLP.

#### - `blocknumber`: [`Number`](./common_types.md#number)

Block number.

#### - `transactions`: [`List`](./common_types.md#list)`[`[`FixtureTransaction`](#fixturetransaction)`]`

List of decoded transactions included in the block RLP.

#### - `uncleHeaders`: [`List`](./common_types.md#list)`[`[`FixtureHeader`](#fixturetransaction)`]`

List of uncle headers included in the block RLP. An empty list post merge.

#### - `withdrawals`: [`Optional`](./common_types.md#optional)`[`[`List`](./common_types.md#list)`[`[`FixtureWithdrawal`](#fixturewithdrawal)`]]` `(fork: Shanghai)`

Optional list of withdrawals included in the block RLP.

### `InvalidFixtureBlock`

#### - `expectException`: [`TransactionException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.TransactionException)` | `[`BlockException`](../../library/ethereum_test_exceptions.md#ethereum_test_exceptions.BlockException)

Expected exception that invalidates the block.

#### - `rlp`: [`Bytes`](./common_types.md#bytes)

RLP serialized version of the block.

#### - `rlp_decoded`: [`Optional`](./common_types.md#optional)`[`[`FixtureBlock`](#fixtureblock)`]`

Decoded block attributes included in the block RLP.

### `FixtureTransaction`

#### - `type`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Transaction type.

#### - `chainId`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Chain ID of the transaction.

#### - `nonce`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Nonce of the account that sends the transaction

#### - `gasPrice`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Gas price for the transaction (Transaction types 0 & 1)

#### - `maxPriorityFeePerGas`: [`HexNumber`](./common_types.md#hexnumber) `(fork: London)`

Max priority fee per gas to pay (Transaction types 2 & 3)

#### - `maxFeePerGas`: [`HexNumber`](./common_types.md#hexnumber) `(fork: London)`

Max base fee per gas to pay (Transaction types 2 & 3)

#### - `gasLimit`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Gas limit of the transaction

#### - `to`: [`Address`](./common_types.md#address)`| null`

Destination address of the transaction, or `null` to create a contract

#### - `value`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Value of the transaction

#### - `data`: [`Bytes`](./common_types.md#bytes)

Data bytes of the transaction

#### - `accessList`: [`List`](./common_types.md#list)`[`[`Mapping`](./common_types.md#mapping)`[`[`Address`](./common_types.md#address)`,`[`List`](./common_types.md#list)`[`[`Hash`](./common_types.md#hash)`]]]` `(fork: Berlin)`

Account access lists (Transaction types 1, 2 & 3)

#### - `maxFeePerBlobGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

Max fee per blob gas to pay (Transaction type 3)

#### - `blobVersionedHashes`: [`List`](./common_types.md#list)`[`[`Hash`](./common_types.md#hash)`]` `(fork: Cancun)`

Max fee per blob gas to pay (Transaction type 3)

#### - `v`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

V value of the transaction signature

#### - `r`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

R value of the transaction signature

#### - `s`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

S value of the transaction signature

#### - `sender`: [`Address`](./common_types.md#address)

Sender address of the transaction

#### - `secretKey`: [`Hash`](./common_types.md#hash)

Private key that must be used to sign the transaction

### `FixtureWithdrawal`

#### - `index`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Index of the withdrawal

#### - `validatorIndex`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Withdrawing validator index

#### - `address`: [`Address`](./common_types.md#address)

Address to withdraw to

#### - `amount`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Amount of the withdrawal
