# Mempool Tests (Draft) <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

!!! warning "Draft"
    This format is a draft under discussion, and its fields may change.

The Mempool Test fixture format tests are included in the fixtures subdirectory `mempool_tests`.

These are produced by the `MempoolTest` test spec.

## Description

The mempool test fixture format is used to test a client's transaction pool admission: given a chain head, its state, and a single transaction received from a peer, whether the client admits the transaction as executable and broadcasts it.

It does so by defining the chain head, the state at the head, the network encoding of the transaction, and whether the transaction must be broadcast. The pool is empty when the transaction arrives, so the outcome never depends on other pooled transactions. The pool validates the transaction against the head state and the next block derived from the head.

The format works with every transaction type. For [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transactions, it also covers the public mempool rules for the validation prefix, which refuse some transactions that are valid in a block.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`Fixture`](#fixture) test object, with the key string representing the test name.

The JSON file path plus the test name are used as the unique test identifier.

## Consumption

For each [`Fixture`](#fixture) test object in the JSON fixture file, perform the following steps:

1. Configure the fork schedule so that [`network`](#-network-fork) is active for both the head block and the next block.
2. Initialize a chain whose head block is [`head`](#-head-fixturehead), with [`pre`](#-pre-alloc) as its state.
3. Create an empty pool, configured with the values in [`policy`](#-policy-fixturepolicy).
4. Decode [`txbytes`](#-txbytes-bytes) using the network (pooled) encoding.
5. Submit the transaction to the pool as a **remote** transaction, as if a peer had sent it.
6. Read the pool's status for the transaction:
    - If [`broadcast`](#-broadcast-bool) is `true` and the transaction is not executable (pending), fail the test.
    - If [`broadcast`](#-broadcast-bool) is `false` and the transaction is executable (pending), fail the test. A transaction kept in a non-executable tier (queued) or rejected both pass.

The test is consumed through a client command (for example `evm mempooltest <fixture.json>`), not through a running node:

- Each test gets a fresh, in-memory pool. Nothing is shared between tests.
- The command starts no peers, no RPC server, and no transaction journal.
- The current time is `head.timestamp`, not the wall clock.
- The output has one entry per test, with the test name, whether the transaction became executable, the client's error if any, and a pass/fail verdict.

A hash returned by `eth_sendRawTransaction` is not evidence of a `true` outcome, because clients also return one for queued transactions.

## Structures

### `Fixture`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork that is active at the head block and at the next block.

#### - `config`: [`FixtureConfig`](./state_test.md#fixtureconfig)

Chain configuration, including the chain ID and the blob schedule.

#### - `head`: [`FixtureHead`](#fixturehead)

Chain head the pool validates against.

#### - `nextBlock`: [`FixtureNextBlock`](#fixturenextblock)

Values of the next block derived from `head`, so consumers can check their own derivation. They are not inputs.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

State at the head block.

#### - `txbytes`: [`Bytes`](./common_types.md#bytes)

Network encoding of the transaction under test.

#### - `transaction`: `Mapping`

Decoded fields of the transaction, for readability. Consumers use only `txbytes`.

#### - `policy`: [`FixturePolicy`](#fixturepolicy)

Pool configuration the consumer must apply.

#### - `broadcast`: `bool`

Whether the client must admit the transaction as executable and announce it to its peers.

#### - `mempoolRuleset`: `str`

Versioned name of the admission rule set the expectation assumes, for example `public-mempool-v1`. A consumer that implements a different rule set, or another version of it, reports the test as skipped, not failed.

#### - `_info.mempool.rules`: `List[str]`

IDs of the admission rules the test exercises, within `mempoolRuleset`, for example `["FRAME_TRANSACTION_VALIDATION_PREFIX_BANNED_OPCODE"]`. When the transaction is valid for the next block but not broadcast, these are the rules it breaks. Consumers do not check them.

#### - `_info.mempool.exception`: [`TransactionException`](../../library/execution_testing_exceptions.md#execution_testing.exceptions.TransactionException)

Exception the specification raises for the transaction in the next block. Missing when the transaction is valid. Consumers do not check it.

#### - `_info.mempool.expectationSource`: `str`

Where the expected outcome comes from: `specification` (checked against the specification when filling) or `author` (a refusal by an admission rule, asserted by the test author). Consumers do not use it.

### `FixtureHead`

#### - `number`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `timestamp`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `gasLimit`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `gasUsed`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `baseFeePerGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: London)`

#### - `excessBlobGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

#### - `blobGasUsed`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

### `FixtureNextBlock`

#### - `number`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `timestamp`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `baseFeePerGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: London)`

#### - `excessBlobGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

### `FixturePolicy`

#### - `minTip`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Minimum priority fee per gas the pool requires.
