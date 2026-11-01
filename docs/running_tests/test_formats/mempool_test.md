# Mempool Tests (Draft) <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

!!! warning "Prototype"
    This format is a proposal under discussion. It is not produced by `fill` yet, and its fields may change. Feedback is welcome.

The Mempool Test fixture format would be stored in the fixtures subdirectory `mempool_tests`, produced by a new `MempoolTest` test spec.

## Description

The mempool test fixture format checks transaction pool admission: given a chain head, a state, and a single transaction received from the network, should the client accept the transaction into its pool and broadcast it to its peers?

Each test vector contains exactly one transaction and a binary expectation. There are no transactions in the pool before the test starts, so the result never depends on previously pooled transactions, replacement rules, eviction, or ordering. Scenarios that need prior pool content (replace-by-fee, per-account slot limits, overdraft across queued transactions, the in-flight limit for delegated accounts), as well as the frame transaction rules that count pending transactions per sender or paymaster) are out of scope for this format. The format works with every transaction type, including frame transactions (see [Frame transactions](#frame-transactions)).

The format reuses most of the [State Test](./state_test.md) building blocks (`pre`, `config`, a signed transaction, and an expected exception). The main difference is that the environment describes the **current chain head**, not the block in which the transaction executes. A transaction pool validates incoming transactions against the head state and derives the values of the next block from the head.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`Fixture`](#fixture) test object, with the key string representing the test name. The JSON file path plus the test name are used as the unique test identifier.

## What "accepted" means

Clients usually have two tiers inside the pool: transactions that are executable on top of the head (pending), and transactions that are kept but not executable yet (queued, for example because of a nonce gap). Only executable transactions are announced to peers.

This format therefore defines the expected outcome as one boolean, [`broadcast`](#-broadcast-bool):

- `true`: the client must admit the transaction as executable and announce it to its peers.
- `false`: the client must not announce the transaction. Whether it is dropped or kept in a non-executable tier is left to the client.

A transaction with a future nonce is a `broadcast: false` test. Geth's legacy pool queues it and its blob pool rejects it, and both behaviors pass.

An `eth_sendRawTransaction` call returning a hash is **not** evidence of a `true` outcome, because clients also return a hash for queued transactions.

## Rule categories

A mempool admission check contains three kinds of rules, and the format handles each one differently.

| Category | Examples | Source of truth for the expectation |
| --- | --- | --- |
| Consensus-derived | Invalid signature, intrinsic gas too low, nonce too low, insufficient balance for the maximum cost, sender has non-delegation code, type not active in the fork, gas limit above the per-transaction cap, blob count above the per-block maximum, `maxFeePerBlobGas` below the next blob base fee | The specification: the transaction must fail `check_transaction` against the next block environment |
| Mempool-only, but uniform across clients | Nonce gap (not executable), missing or malformed blob sidecar, wrong sidecar version for the fork, invalid KZG proofs, set-code transaction with an empty authorization list | Asserted by the test author with a mempool-specific exception |
| Node policy | Minimum tip, maximum transaction size, `maxFeePerGas` below the next base fee, pool capacity | Not tested in the first iteration; fixtures stay clear of these limits (see [`policy`](#-policy-fixturepolicy)) |

The consensus-derived category gives `fill` an oracle. For every fixture with `broadcast: true`, the filler runs the transaction through the specification's `check_transaction` against the next block environment and fails the fill if the transaction is invalid. For every rejection whose exception is a `TransactionException`, the filler checks that the specification raises it. Mempool-only rejections are new `MempoolException` values that the specification cannot verify, so they rely on review.

## Consumption

For each [`Fixture`](#fixture) test object in the JSON fixture file, perform the following steps:

1. Configure the fork schedule so that [`network`](#-network-fork) is active for both the head block and the next block.
2. Initialize the chain with [`head`](#-head-fixtureheader) as the genesis (head) block and [`pre`](#-pre-alloc) as its state. `head.stateRoot` must equal the state root of `pre`.
3. Configure the pool with the values in [`policy`](#-policy-fixturepolicy).
4. Decode [`txbytes`](#-txbytes-bytes) using the network (pooled) encoding. For blob transactions, this encoding includes the sidecar.
5. Submit the transaction to the pool as a **remote** transaction, as if a peer had sent it. Transactions submitted locally may be exempt from some checks.
6. Observe whether the client considers the transaction executable and announces it:
    - If [`broadcast`](#-broadcast-bool) is `true` and the transaction is not executable or not announced, fail the test.
    - If [`broadcast`](#-broadcast-bool) is `false` and the transaction is announced, fail the test.
7. Optionally, if [`exception`](#-exception-transactionexception-mempoolexception) is present and the client rejected the transaction, compare the rejection reason with it using the client's exception mapper. A mismatch is reported but does not fail the test while the format is a prototype.

### Direct consumption

Similar to `consume direct` for state tests, a client binary can run the fixture in-process. It builds the pool on top of an in-memory state and reads the pool's status for the transaction hash, without any networking. This approach is quick and is the recommended first consumer.

### Hive consumption

A Hive simulator starts the client with a genesis built from `head`, `pre`, and `config`, and connects two devp2p peers controlled by the simulator. Peer A sends the transaction (a full `Transactions` message, or an announcement followed by a `PooledTransactions` response for blob transactions). Peer B waits for a `NewPooledTransactionHashes` announcement that contains the hash. If no announcement arrives within a timeout, the outcome is `false`. This mode tests the full network path, but its negative results depend on a timeout. A positive-control transaction in the same session would make it more reliable, at the cost of making the session more than a single-transaction test.

## Structures

### `Fixture`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork that is active at the head block and at the next block. Fork transitions are out of scope for the first iteration (see [Open questions](#open-questions)).

#### - `config`: [`FixtureConfig`](./state_test.md#fixtureconfig)

Chain configuration, including the chain ID and the blob schedule.

#### - `head`: [`FixtureHeader`](./blockchain_test.md#fixtureheader)

The current chain head. Its `number`, `timestamp`, `gasLimit`, `gasUsed`, `baseFeePerGas`, `excessBlobGas`, and `blobGasUsed` determine the next block environment the pool validates against. The filler sets `gasUsed` and `blobGasUsed` so that the next base fees match the values the test author chose.

#### - `nextBlock`: [`FixtureNextBlock`](#fixturenextblock)

Values of the next block derived from `head`, included so consumers can check their own derivation. Consumers do not use them as inputs.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

State at the head block.

#### - `txbytes`: [`Bytes`](./common_types.md#bytes)

Network encoding of the transaction under test. For blob transactions, this is the wrapper with blobs, commitments, and proofs, using the sidecar version of `network`.

#### - `transaction`: `Mapping`

Decoded fields of the transaction, for readability and debugging, in the representation the framework uses for the transaction's type. For types 0–4 this is a [`FixtureTransaction`](./state_test.md#fixturetransaction) where each list-valued field contains exactly one element. For frame transactions it contains `sender`, `nonce`, `frames`, `signatures`, `fees`, and `blobVersionedHashes`. Consumers use only `txbytes` as input.

#### - `policy`: [`FixturePolicy`](#fixturepolicy)

Pool configuration that the consumer must apply.

#### - `broadcast`: `bool`

Whether the client must admit the transaction as executable and announce it to its peers.

#### - `exception`: [`TransactionException`](../../library/execution_testing_exceptions.md#execution_testing.exceptions.TransactionException) | `MempoolException`

Expected reason for the rejection. The field is missing when `broadcast` is `true`, and optional for nonce-gap tests, where a client may keep the transaction queued instead of rejecting it.

### `FixtureNextBlock`

#### - `number`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `timestamp`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `baseFeePerGas`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

#### - `blobBaseFee`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber) `(fork: Cancun)`

### `FixturePolicy`

#### - `minTip`: [`ZeroPaddedHexNumber`](./common_types.md#zeropaddedhexnumber)

Minimum priority fee per gas the pool requires. Fixtures in the first iteration set it to `0x00`, and all transactions pay a tip well above common client defaults, so a client that cannot lower its minimum still passes.

## Frame transactions

The format does not depend on the transaction type: `txbytes` carries any [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) transaction, including frame transactions (type `0x06`, [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)). Frame transactions are where this format is most useful. For types 0–4, the pool checks the transaction's fields against the sender's account. A frame transaction's validity is decided by EVM code, so the pool has to simulate its validation prefix before it can propagate the transaction. Unlike most legacy pool behavior, EIP-8141 writes these public mempool rules into the EIP. Every client is expected to apply them the same way, which makes them good candidates for shared tests.

### Rules that fit a single-transaction test

Most of the EIP's public mempool rules depend only on the transaction and the head state, so the format can test them without changes:

- **Prefix recognition.** The validation prefix must match one of the recognized shapes (`[self_verify]`, `[deploy, self_verify]`, `[only_verify, pay]`, `[deploy, only_verify, pay]`, optionally preceded by an expiry verifier). No `VERIFY` frame may follow it, no prefix frame may carry `ATOMIC_BATCH_FLAG`, and `deploy` must come first. Each shape is a positive test, and each violation is a negative test.
- **Validation gas caps.** `MAX_VERIFY_GAS` (execution limits in the prefix plus signature verification cost) and `MAX_VERIFY_STATE_GAS`. These need boundary tests at the cap and one unit over it.
- **Banned opcodes.** One parametrized test per banned opcode (`GASPRICE`, `BLOCKHASH`, `COINBASE`, `TIMESTAMP`, `NUMBER`, `PREVRANDAO`, `GASLIMIT`, `BASEFEE`, `BLOBBASEFEE`, `SLOTNUM`, `GAS`, `CREATE`, `CREATE2`, `SETDELEGATE`, `INVALID`, `SELFDESTRUCT`, `BALANCE`, `SELFBALANCE`, `SSTORE`) executed in a verify frame, directly or through a nested call. Each exception gets a positive test: `GAS` directly before a `*CALL`, `TIMESTAMP` in the canonical expiry verifier, and `CREATE`/`CREATE2`/`SETDELEGATE`/`SSTORE` to `tx.sender` in the first `deploy` frame.
- **State access.** `SLOAD` outside `tx.sender`'s storage, including through transitive calls. Writes other than the allowed deploy writes. `CALL*`/`EXTCODE*` to an address that is empty or delegated through EIP-7702. The contracts that the verify frames call are deployed in `pre`.
- **Approval outcome.** A prefix frame reverts, exits without its required `APPROVE`, uses a scope its flags do not allow, or never sets the payer. Some of these cases also make the transaction invalid by consensus, so the filler can check them against the specification (see below).
- **Expiry.** The canonical expiry verifier with a deadline before, at, and after the head timestamp. The EIP refers to the node's view of the current block timestamp, so the fixture defines that view as `head.timestamp`. A consumer must use the head timestamp, not the wall clock. This needs care in Hive, where the wall clock is far ahead of the genesis timestamp.
- **Paymaster solvency with an empty pool.** With nothing pending, `available_paymaster_balance` reduces to `balance - pending_withdrawal_amount`. Both values come from `pre`, where the canonical paymaster is deployed with its exact runtime code. The tests cover a canonical paymaster that is solvent, one that is insolvent only because of a pending withdrawal, a non-canonical paymaster subject to the trace rules, and a default-code payer.
- **Signatures.** Each signature scheme (`ARBITRARY`, `SECP256K1`, `P256`) with a valid and an invalid signature, and the all-zero explicit digest.

### Rules that need pool content

The following rules depend on transactions that are already pending, so this format does not cover them. A future multi-transaction format could:

- At most one pending transaction per sender, and replacement by `(sender, nonce)` with the fee bump.
- `MAX_PENDING_TXS_USING_NON_CANONICAL_PAYMASTER` and the `reserved_pending_cost` term of paymaster solvency.
- The per-payer exposure rule for default-code payers.
- Eviction order and re-simulation after a new head.

Re-simulation after a new head could fit a two-step extension of this format: admit the transaction, apply one block that touches a dependency (for example a sender storage slot that the prefix read), and expect the transaction to be dropped. That is still one transaction under test, but it is not part of the first iteration.

### Fixture additions

- `MempoolException` gains frame-specific values, for example `FRAME_PREFIX_NOT_RECOGNIZED`, `FRAME_VALIDATION_BANNED_OPCODE`, `FRAME_VALIDATION_STORAGE_ACCESS`, `FRAME_VALIDATION_GAS_EXCEEDED`, `FRAME_EXPIRED`, and `PAYMASTER_INSUFFICIENT_BALANCE`.
- No new fixture fields are needed. Every input is already in `head`, `pre`, and `txbytes`, and the gas caps are protocol constants of the fork.

### Specification oracle

The consensus check in `fill` still applies: a frame transaction with `broadcast: true` must pass the specification's frame transaction check against the next block environment. However, the trace rules (banned opcodes, storage access, gas caps, prefix shapes) are not consensus, so the specification cannot verify those expectations today.

The FOCIL-with-frames work already contains a related specification. `inclusion_list_frames.py` in the `eips/bogota/focil-frames` branch classifies frame candidates and replays their validation prefix on a disposable state. Its constants and rules differ from the mempool rules (for example `MAX_VERIFY_GAS_PER_TX = 2**18` against the mempool's `MAX_VERIFY_GAS = 100_000`), so it cannot be used as the oracle as it is. Still, it shows that a `validate_pooled_frame_transaction` function using the same frame interpreter with a trace hook is feasible. With such a function, `fill` could compute `broadcast` and `exception` for every frame test instead of relying on the test author. This is the strongest argument for the "specification for mempool rules" open question below.

### Consumer impact

The format adds no consumer work for frame transactions: a direct consumer still decodes `txbytes`, submits the transaction as remote, and checks whether it is pending. The cost is in the client's own frame transaction pool, which has to simulate the prefix with a tracer. A geth consumer would register the frame subpool next to the legacy and blob subpools when building `txpool.New`, and needs no other changes. The local go-ethereum checkout used for this estimate has no frame transaction support yet.

## Writing tests

A test would look like a state test that uses a different filler fixture and has no post-state:

```python
@pytest.mark.valid_from("Cancun")
def test_nonce_too_low(mempool_test: MempoolTestFiller, pre: Alloc) -> None:
    """Reject a transaction whose nonce is below the account nonce."""
    sender = pre.fund_eoa(nonce=1)
    tx = Transaction(
        sender=sender,
        nonce=0,
        to=pre.fund_eoa(amount=0),
        gas_limit=21_000,
    )
    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=TransactionException.NONCE_MISMATCH_TOO_LOW,
    )
```

A `mempool_test` call accepts an optional `head` environment (base fee, excess blob gas, gas limit, timestamp). Many existing invalid-transaction state tests could also produce a mempool fixture, because a transaction that is invalid for the next block must not be broadcast. The exceptions are rules where the two outcomes differ: a nonce gap is valid in the pool but invalid in a block, and a fee cap below the base fee is a policy question.

## Implementing a consumer in go-ethereum

Geth already contains almost every piece a direct consumer needs. The estimate below is based on the current `core/txpool` code.

### Building blocks that already exist

- `tests.MakePreState` (`tests/state_test_util.go`) builds a `StateDB` from an `Alloc`, and `tests.Forks` maps fork names to chain configurations.
- `legacypool.BlockChain` is a small interface (`Config`, `CurrentBlock`, `Genesis`, `GetBlock`, `StateAt`). The pool tests already stub it in about 40 lines (`testBlockChain` in `core/txpool/legacypool/legacypool_test.go`).
- `txpool.New(gasTip, chain, []SubPool{legacyPool, blobPool})` constructs the full pool. `TxPool.Add([]*types.Transaction{tx}, true)` submits a transaction as remote and synchronously, and `TxPool.Status(hash)` returns `TxStatusPending` or `TxStatusQueued`. Mapping `TxStatusPending` to `broadcast: true` matches when geth announces transactions, because geth announces them on promotion to pending.
- `types.Transaction.UnmarshalBinary` decodes the pooled blob transaction encoding including the sidecar.
- `cmd/evm` already has `statetest` and `blocktest` runners that `consume direct` drives. A `mempooltest` subcommand would follow the same pattern, and EEST would add a `consume_mempool_test` method to `GethFixtureConsumer` (`packages/testing/src/execution_testing/client_clis/clis/geth.py`).

### New work

1. JSON types for the fixture, generated with `gencodec` like the state test types (about 100 lines).
2. A runner (about 200–300 lines) that builds the state and a stub chain whose head is `fixture.head`, creates the legacy and blob subpools with `policy` applied (`PriceLimit`, and a temporary data directory for the blob pool), calls `Add`, and checks `Status`.
3. A `cmd/evm mempooltest` subcommand with JSON output in the shape `consume direct` expects (about 100 lines).
4. Exception mapping: add `MempoolException` entries to the EEST geth exception mapper. Geth's errors are already distinct sentinels (`core.ErrNonceTooLow`, `txpool.ErrInvalidSender`, `txpool.ErrSidecarFormatError`, and others), so this is a table of substrings.

The total is roughly 400–600 lines of Go plus a small Python change. A developer who knows geth could deliver it in a few days. The blob pool setup (data directory, reserver, KZG) takes the most effort, and a first version could cover only the legacy pool and add blob transactions later.

### Behaviors the tests would expose

These are places where geth's behavior and the format's definition may diverge. Finding such divergences is the purpose of the tests:

- **Head rules, not next-block rules.** `txpool.ValidateTransaction` derives the fork rules from the head header (`head.Number`, `head.Time`) and checks `tx.Gas()` against `head.GasLimit`. At a fork boundary, or when the next block's gas limit differs, the result may differ from the specification's next-block check. This is why the first iteration excludes transitions.
- **No base fee check.** Geth does not compare `maxFeePerGas` with the next base fee during admission, so such transactions become pending and are announced. Other clients may reject them. This is why the format treats the comparison as node policy.
- **Local versus remote.** Transactions submitted through `eth_sendRawTransaction` pass through the locals tracker. A direct consumer must call `TxPool.Add` as a remote submission to match what a peer would see.

## Open questions

- **Fork transitions.** Should the pool use the head fork or the next block's fork? A transition variant (for example `network: "PragueToOsakaAtTime15k"` with the head just before the boundary) would make the expectation explicit, but clients first need to agree on the answer.
- **Fee cap below base fee.** Should this rule move from policy to the uniform category, and in which direction?
- **A specification for mempool rules.** The mempool-only rules could be written down in the specification as non-consensus helpers (for example a `validate_pooled_transaction` function next to `check_transaction`). The filler could then verify every expectation instead of relying on review. Frame transactions need this the most, because their admission rules are long, written in the EIP, and depend on tracing EVM execution.
- **Rejection reasons.** Should the exception become a hard check once client mappers exist, or always stay informational?
- **Relation to the devp2p `eth` suite.** Hive's `devp2p` simulator already has `TestInvalidTxs` and `TestBlobViolations`, which send transactions over the wire and check that they are not propagated. A Hive consumer for this format could reuse that connection code.
