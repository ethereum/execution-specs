# Mempool Tests (Draft) <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

!!! warning "Prototype"
    This format is a proposal under discussion. It is not produced by `fill` yet, and its fields may change. Feedback is welcome.

The Mempool Test fixture format would be stored in the fixtures subdirectory `mempool_tests`, produced by a new `MempoolTest` test spec.

## Description

The mempool test fixture format checks transaction pool admission: given a chain head, a state, and a single transaction received from the network, should the client accept the transaction into its pool and broadcast it to its peers?

Each test vector contains exactly one transaction and a binary expectation. There are no transactions in the pool before the test starts, so the result never depends on previously pooled transactions, replacement rules, eviction, or ordering. Scenarios that need prior pool content are left to a separate, later format (see [Scope: single transaction versus existing pool content](#scope-single-transaction-versus-existing-pool-content)). The format works with every transaction type, including frame transactions (see [Frame transactions](#frame-transactions)).

The format reuses most of the [State Test](./state_test.md) building blocks (`pre`, `config`, a signed transaction, and an expected exception). The main difference is that the environment describes the **current chain head**, not the block in which the transaction executes. A transaction pool validates incoming transactions against the head state and derives the values of the next block from the head.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`Fixture`](#fixture) test object, with the key string representing the test name. The JSON file path plus the test name are used as the unique test identifier.

## What "accepted" means

Clients usually have two tiers inside the pool: transactions that are executable on top of the head (pending), and transactions that are kept but not executable yet (queued, for example because of a nonce gap). Only executable transactions are announced to peers.

This format therefore defines the expected outcome as one boolean, [`broadcast`](#-broadcast-bool):

- `true`: the client must admit the transaction as executable and announce it to its peers.
- `false`: the client must not announce the transaction. Whether it is dropped or kept in a non-executable tier is left to the client.

A transaction with a future nonce is a `broadcast: false` test. Geth's legacy pool queues it and its blob pool rejects it, and both behaviors pass.

The consumer command reads this outcome from the pool's own status for the transaction, not from the network (see [Command-based consumption](#command-based-consumption)). An `eth_sendRawTransaction` call returning a hash is **not** evidence of a `true` outcome, because clients also return a hash for queued transactions.

## Rule categories

A mempool admission check contains three kinds of rules, and the format handles each one differently.

| Category | Examples | Source of truth for the expectation |
| --- | --- | --- |
| Consensus-derived | Invalid signature, intrinsic gas too low, nonce too low, insufficient balance for the maximum cost, sender has non-delegation code, type not active in the fork, gas limit above the per-transaction cap, blob count above the per-block maximum, `maxFeePerBlobGas` below the next blob base fee | The specification: the transaction must fail `check_transaction` against the next block environment |
| Mempool-only, but uniform across clients | Nonce gap (not executable), missing or malformed blob sidecar, wrong sidecar version for the fork, invalid KZG proofs, set-code transaction with an empty authorization list | Asserted by the test author with a mempool-specific exception |
| Node policy | Minimum tip, maximum transaction size, `maxFeePerGas` below the next base fee, pool capacity | Not tested in the first iteration; fixtures stay clear of these limits (see [`policy`](#-policy-fixturepolicy)) |

Only the consensus-derived category can be checked against the specification. The next section discusses what that means for the correctness of the tests.

## Correctness of expected outcomes

The specification describes consensus only, so it has no place for mempool rules today and cannot simulate a mempool test. For a state test, `fill` runs the specification and writes down the result, so the expected outcome is correct by construction. For a mempool test, the test author decides the outcome in most cases. The outcome is only confirmed when the fixture runs against a client that implements the rule. If the author's reading of the rule is wrong, the fixture is wrong, and the first client to run it may get a failure that is the test's fault.

This is the largest risk of the format. The rest of this section looks at how much of it remains and how to reduce it.

### How much can be checked when filling

| Expectation | Check available when filling | Remaining risk |
| --- | --- | --- |
| `broadcast: true` | Necessary condition: the specification's `check_transaction` (or the frame transaction check) passes against the next block environment. It does not prove that no mempool-only rule rejects the transaction. | Low to medium |
| `broadcast: false` with a `TransactionException` | Full: the specification rejects the transaction for the next block, so the transaction cannot be executable. | Low |
| Nonce gap | Full: computed from `pre`. | Low |
| Blob sidecar format and KZG proofs | Partial: the framework's blob helpers can recompute cells, commitments, and proofs, which confirms that the sidecar is valid or invalid as claimed. Whether clients reject a given malformation is still the author's reading. | Medium |
| EIP-8141 trace rules (prefix shapes, banned opcodes, state access, validation gas caps, expiry, paymaster) | None. | High |

The risk is highest for frame transactions, which are also the main reason for having the format.

### Reducing the risk without a mempool specification

- **Record where each expectation comes from.** Each fixture's `_info` states the source of its expectation: `specification`, `framework` (computed from the inputs, such as a nonce gap or a KZG check), or `author`. When a client fails an `author` fixture, the client team and the test author both know that the test itself is one of the suspects.
- **Minimal pairs.** Every `author` negative test comes with a positive twin that differs only in the rule under test, for example the same verify frame without the banned opcode. The twin's `broadcast: true` is checked against the specification, so the negative test cannot fail for an unrelated reason, such as a balance too low to pay for the transaction. A wrong assumption is then limited to the one rule the pair is about.
- **Cite the rule.** Every `author` test references the normative text it implements, for example the relevant part of the EIP-8141 mempool section. For types 0–4, a rule with no normative text is a sign that it is client policy and should not be tested in this format.
- **Agreement between clients before release.** `author` fixtures are released as candidates and become part of a release only after at least two independent client implementations pass them. A disagreement is triaged as a test bug, a client bug, or an ambiguity in the EIP. The last case is useful in itself, because it means the EIP needs clarifying. This is weaker than a specification check: two clients can share a misreading, and early on only one client may implement the frame transaction pool.

### Writing the rules down

The rules can only be checked mechanically if they are written as code somewhere. There are three options:

1. **A non-consensus module in the specification**, for example a `mempool.py` next to `fork.py` in each fork, defining `validate_pooled_transaction`. It would get the same review as the specification and would follow its fork-by-fork copying. It also expands the repository beyond consensus, and that decision belongs to the specification maintainers.
2. **A reference checker in the testing framework** (`execution_testing`). It would reuse the specification's frame interpreter with a trace hook to apply the EIP-8141 prefix rules, and `fill` would use it to compute or verify `broadcast` and `exception`. The bar is lower and it can start now, but it is test code: a bug in it produces wrong fixtures with confidence, so it needs the same agreement between clients as above until it has proven itself.
3. **No code.** The rules stay in EIP text, and every non-consensus expectation is `author`.

The recommendation is to start with option 3 plus the mitigations above for the first fixtures. In parallel, build option 2 for the EIP-8141 trace rules, which are the most error-prone to hand-write and the most valuable to automate. Option 2 can later move into the specification (option 1) if the maintainers want mempool rules there. The FOCIL-with-frames work (see [Specification oracle](#specification-oracle)) shows that replaying a validation prefix on top of the specification's interpreter is practical.

## Scope: single transaction versus existing pool content

Mempool behavior splits into two families of tests:

- **Single-transaction admission**: the pool is empty, one transaction arrives, and the test checks whether the client broadcasts it. This document defines that format.
- **Pool-content tests**: the pool already holds transactions, or receives several in sequence, and the outcome of the new transaction depends on them. Examples are replacement, per-sender limits, and eviction.

The two families differ enough to justify separate formats. This document studies only the feasibility of the first. The second needs its own analysis. The sections below explain where the line falls, why the single-transaction format is feasible now, and what this format does to keep the pool-content format possible.

### What each family covers

| Rule | Single transaction | Needs pool content |
| --- | --- | --- |
| Signature, intrinsic gas, fee fields, type active in the fork, gas caps | Yes | |
| Nonce too low, nonce gap (not broadcast), balance against maximum cost | Yes | |
| Blob sidecar format, version, and KZG proofs | Yes | |
| EIP-8141 prefix shapes, validation gas caps, banned opcodes, state access, expiry | Yes | |
| EIP-8141 paymaster solvency with nothing reserved | Yes | |
| Replacement by `(sender, nonce)` and the minimum fee bump | | Yes |
| Overdraft across several pending transactions from one sender | | Yes |
| Per-sender and per-account slot limits | | Yes |
| In-flight limit for EIP-7702 delegated senders | | Yes |
| EIP-8141 one pending transaction per sender, `MAX_PENDING_TXS_USING_NON_CANONICAL_PAYMASTER`, reserved paymaster cost, per-payer exposure | | Yes |
| Promotion of a queued transaction once its nonce gap is filled | | Yes |
| Eviction order when the pool is full | | Yes |
| Re-validation and removal after a new head | | Yes (or one transaction plus one block) |

Most of the rules a client checks when a transaction arrives are in the first column. The rules that need pool content are mostly about how the pool manages its resources over time.

### Why the single-transaction format is feasible

- **The starting point is the same for every client.** An empty pool on top of a given head and state is the same starting point in every client. With prior content, the starting point depends on how each client stored, ordered, and possibly already evicted the earlier transactions.
- **The outcome is one observation.** The test reads whether the pool holds the transaction as executable. It needs no second query, no ordering, and no knowledge of the pool's internal tiers. A queued or dropped future-nonce transaction passes in both cases.
- **The spec can check the expected results.** For consensus-derived rules, `fill` checks every expectation against `check_transaction`. Pool-content rules have no consensus counterpart at all.
- **Clients already validate this way.** Geth calls `ValidateTransaction` without state and `ValidateTransactionWithState` with state, and with an empty pool the pool callbacks return zero or nothing. A consumer adds no new behavior to the client: it calls the code the network path already uses.
- **The format reuses existing building blocks.** `pre`, `config`, the headers, and the exception mappers already exist for state and blockchain tests.

### Remaining risks for the single-transaction format

These affect feasibility but do not block it:

- **The pool must be truly empty.** The consumer is a command that builds a fresh in-memory pool for every test, with no journal, peers, or RPC, so the empty starting pool is guaranteed by construction. This is a requirement on the command, and the reason the format is not consumed through Hive (see [Why not Hive (for now)](#why-not-hive-for-now)).
- **Policy defaults.** Minimum tip and size limits differ between clients. The format avoids their boundaries instead of testing them (see [`policy`](#-policy-fixturepolicy)).
- **Head versus next block.** Clients may use the fork rules or gas limit of the head where the specification uses the next block. This is why transitions are excluded at first.
- **The network path is not tested.** The command skips wire decoding, the transaction fetcher, and the announcement logic. These are outside admission and are better covered by the devp2p `eth` suite in Hive.
- **Expected outcomes the specification cannot check.** Outside the consensus-derived rules, the test author decides the expected outcome, and it is only confirmed by running a client. See [Correctness of expected outcomes](#correctness-of-expected-outcomes).
- **Coverage, not correctness.** A client that ignores a pool-content rule (for example, it accepts a second pending frame transaction from the same sender) passes every single-transaction test. The single-transaction format does not catch that. The later format does.

### Keeping the pool-content format possible

The single-transaction format should be a special case of the later format, not a dead end. These choices in this draft are meant to keep that possible:

- **Shared inputs.** `network`, `config`, `head`, `pre`, and `policy` describe the node before any transaction arrives. A pool-content fixture needs exactly the same inputs, so it should reuse these structures unchanged.
- **The result belongs to one transaction.** `txbytes`, `broadcast`, and `exception` together describe one transaction and its outcome. A pool-content fixture could become an ordered list of those triples, each with its own expectation. A single-transaction fixture is then the same fixture with a list of length one.
- **Same consumer, run in a loop.** The command built for this format (build the state, build the pool, submit as remote, read the status) becomes the inner step of a pool-content consumer. The new parts are keeping the pool between steps and reading more outcomes.
- **Separate fixture directory.** The later format would use its own directory (for example `mempool_sequence_tests`). Existing consumers then never receive fixtures they cannot run, and this format does not need a version field to tell the two apart.

### Questions the pool-content format needs to answer

These are recorded here so they are not lost. They do not affect the single-transaction format:

- **More outcomes than broadcast.** Replacement and eviction affect transactions that were already announced, and clients do not announce a removal on the network. A command-based consumer avoids the problem: it owns the emulated pool, so it can report the pool's contents after each step as part of its output. A new client endpoint to clear the pool or report its contents is only needed if pool-content tests must also run against a live node in Hive, and that can be decided when the format is designed.
- **Which rules are uniform.** Replacement bumps, slot limits, and pool capacity are client policy for types 0–4. EIP-8141 writes several pool-content rules into the EIP (one pending transaction per sender, the paymaster limits, and the 10% conventional bump), so frame transactions may be the first area where pool-content tests can be shared between clients.
- **Events between transactions.** Re-validation needs new heads between submissions. The format would need block events in the sequence, which brings in the blockchain test machinery.
- **Spec oracle.** Pool-content expectations have no consensus counterpart. Without a specification of the pool rules, every expectation relies on the test author.

## Consumption

For each [`Fixture`](#fixture) test object in the JSON fixture file, perform the following steps:

1. Configure the fork schedule so that [`network`](#-network-fork) is active for both the head block and the next block.
2. Initialize the chain with [`head`](#-head-fixtureheader) as the genesis (head) block and [`pre`](#-pre-alloc) as its state. `head.stateRoot` must equal the state root of `pre`.
3. Configure the pool with the values in [`policy`](#-policy-fixturepolicy).
4. Decode [`txbytes`](#-txbytes-bytes) using the network (pooled) encoding. For blob transactions, this encoding includes the sidecar.
5. Submit the transaction to the pool as a **remote** transaction, as if a peer had sent it. Transactions submitted locally may be exempt from some checks.
6. Read the pool's own decision for the transaction hash: executable (the state in which the client would announce it), or not executable (queued, or rejected):
    - If [`broadcast`](#-broadcast-bool) is `true` and the transaction is not executable, fail the test.
    - If [`broadcast`](#-broadcast-bool) is `false` and the transaction is executable, fail the test.
7. Optionally, if [`exception`](#-exception-transactionexception-mempoolexception) is present and the client rejected the transaction, compare the rejection reason with it using the client's exception mapper. A mismatch is reported but does not fail the test while the format is a prototype.

### Command-based consumption

The format is consumed only through a client command, in the same way `consume direct` drives `evm statetest`. For example, geth would add `evm mempooltest <fixture.json>`. The command guarantees the empty starting pool, which is the main reason for choosing it: every test starts from an emulated pool that the command builds in memory for that test and discards afterwards.

The command must follow this contract:

- **A fresh pool for each test.** For every test object, the command builds the state from `pre`, a chain view whose head is `head`, and a new pool. Nothing is shared between tests, including within one fixture file.
- **No networking and no persistence.** The command starts no peers, no RPC server, no transaction journal, and no re-injection of local transactions. Its only input is the fixture, and its only clock is `head.timestamp`.
- **Remote submission.** The transaction enters through the same validation path as a transaction received from a peer.
- **The pool's own verdict as the output.** The command reports, for each test, whether the transaction ended up executable and the rejection error if there was one. The executable status stands in for the announcement: clients announce a transaction when it becomes executable, so the network layer adds no further admission decision.
- **Machine-readable results.** The output is one JSON entry per test, with the test name, the observed outcome, the error, and a pass/fail verdict. This mirrors what `consume direct` already parses for `statetest`.

Several execution clients already ship a command of this kind for state tests, and `consume direct` already knows how to call them: `evm statetest` in geth and Erigon, `nethtest` in Nethermind, and `evmtool` in Besu. Reth has no `consume direct` integration yet. EVM-only implementations such as evmone have no pool, so they are not consumers of this format. A `mempooltest` subcommand next to `statetest` reuses the client's fixture loading and pre-state building. It only adds the pool construction and the verdict.

### Why not Hive (for now)

A Hive consumer would test the full network path: decoding from the wire, the fetcher, and the announcement. However, this format does not need it:

- **No endpoint guarantees an empty pool.** A Hive client is a full node. Hive can only assume that a freshly started client has an empty pool, and has no standard endpoint to check it or to clear it between tests. Restarting the client for every test would avoid the problem but makes each test cost a full client start.
- **No endpoint reports the verdict.** `eth_sendRawTransaction` returns a hash for queued transactions too, and `txpool_*` methods are not standardized. The only standard signal is a devp2p announcement to a second peer, so a negative result means waiting for a timeout.
- **The clock is not controlled.** Expiry rules and anything else that compares with the current time would see the wall clock in Hive, not `head.timestamp`.

A new endpoint that clears the pool or reports its contents is not needed for single-transaction tests, because the command already provides both guarantees. Hive consumption can be added later as an end-to-end smoke test for a small subset of fixtures (for example one positive and one negative test per transaction type), reusing the devp2p `eth` suite's connection code. It would not be the conformance path.

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

#### - `_info.expectationSource`: `str`

Where the expected outcome comes from: `specification` (checked against the specification when filling), `framework` (computed from the fixture's inputs, such as a nonce gap or a KZG proof check), or `author` (asserted by the test author only). Consumers do not use it. It helps triage failures (see [Correctness of expected outcomes](#correctness-of-expected-outcomes)).

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
- **Expiry.** The canonical expiry verifier with a deadline before, at, and after the head timestamp. The EIP refers to the node's view of the current block timestamp, so the fixture defines that view as `head.timestamp`. The consumer command must use the head timestamp, not the wall clock.
- **Paymaster solvency with an empty pool.** With nothing pending, `available_paymaster_balance` reduces to `balance - pending_withdrawal_amount`. Both values come from `pre`, where the canonical paymaster is deployed with its exact runtime code. The tests cover a canonical paymaster that is solvent, one that is insolvent only because of a pending withdrawal, a non-canonical paymaster subject to the trace rules, and a default-code payer.
- **Signatures.** Each signature scheme (`ARBITRARY`, `SECP256K1`, `P256`) with a valid and an invalid signature, and the all-zero explicit digest.

### Rules that need pool content

The following rules depend on transactions that are already pending, so this format does not cover them. They belong to the later pool-content format (see [Scope](#scope-single-transaction-versus-existing-pool-content)):

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

The FOCIL-with-frames work already contains a related specification. `inclusion_list_frames.py` in the `eips/bogota/focil-frames` branch classifies frame candidates and replays their validation prefix on a disposable state. Its constants and rules differ from the mempool rules (for example `MAX_VERIFY_GAS_PER_TX = 2**18` against the mempool's `MAX_VERIFY_GAS = 100_000`), so it cannot be used as the oracle as it is. Still, it shows that a `validate_pooled_frame_transaction` function using the same frame interpreter with a trace hook is feasible. With such a function, `fill` could compute `broadcast` and `exception` for every frame test instead of relying on the test author. See [Writing the rules down](#writing-the-rules-down) for where that function could live.

### Consumer impact

The format adds no consumer work for frame transactions: the consumer command still decodes `txbytes`, submits the transaction as remote, and checks whether it is pending. The cost is in the client's own frame transaction pool, which has to simulate the prefix with a tracer. A geth consumer would register the frame subpool next to the legacy and blob subpools when building `txpool.New`, and needs no other changes. The local go-ethereum checkout used for this estimate has no frame transaction support yet.

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

Geth already contains almost every piece the consumer command needs. The estimate below is based on the current `core/txpool` code.

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
- **Local versus remote.** Transactions submitted through `eth_sendRawTransaction` pass through the locals tracker. The command must call `TxPool.Add` as a remote submission to match what a peer would see.

## Open questions

- **Fork transitions.** Should the pool use the head fork or the next block's fork? A transition variant (for example `network: "PragueToOsakaAtTime15k"` with the head just before the boundary) would make the expectation explicit, but clients first need to agree on the answer.
- **Fee cap below base fee.** Should this rule move from policy to the uniform category, and in which direction?
- **Where mempool rules live.** Should they be written as a non-consensus module in the specification, a reference checker in the testing framework, or stay in EIP text only? See [Correctness of expected outcomes](#correctness-of-expected-outcomes). Frame transactions need an answer the most, because their admission rules are long and depend on tracing EVM execution.
- **Release policy for `author` fixtures.** How many independent client implementations must pass a fixture before it leaves candidate status, and what happens when only one client implements a rule?
- **Rejection reasons.** Should the exception become a hard check once client mappers exist, or always stay informational?
- **Relation to the devp2p `eth` suite.** Hive's `devp2p` simulator already has `TestInvalidTxs` and `TestBlobViolations`, which send transactions over the wire and check that they are not propagated. If a Hive smoke test is added later (see [Why not Hive (for now)](#why-not-hive-for-now)), it could reuse that connection code.
