# Blockchain Engine Reorg Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Engine Reorg Test fixture format tests are included in the fixtures subdirectory `blockchain_tests_engine_reorg`, and describe a DAG of Engine API payloads plus a branching script of Engine API / JSON-RPC steps to verify chain reorganization behavior.

These are produced by the `ReorgTest` test spec.

## Description

Unlike [`BlockchainEngineFixture`](./blockchain_test_engine.md) (a linear payload list where the consumer always sends `forkchoiceUpdated(head=payload)` after each payload), this format lets a test describe side chains, explicit forkchoice states (head, safe, finalized), multiple legal outcomes per step, outcome-specific follow-up steps (branches), client-built payloads (`getPayload` binds the built payload to a new label), and transaction-pool observations.

Every block in the DAG names its parent by label instead of relying on list order, so sibling blocks and blocks built on top of an invalid block are first-class. Every hash-valued step field is a label (`"genesis"` is reserved for the genesis block, `"zero"` for the zero hash, and `"latest"`/`"null"`/`"any"` are reserved RPC tags/special values valid only where a field's description says so; labels introduced by `getPayload.bind` are resolved at run time); the consumer resolves labels to hashes itself, so fixtures are byte-identical across clients.

Each step's `expect` field is a list of legal outcomes (the [Engine API reference model](../../library/execution_testing_specs.md) fills it in at fill time for any step an author left unannotated, deriving the outcomes the [execution-apis](https://github.com/ethereum/execution-apis) specification allows a conformant client to return); the consumer selects the first outcome matching the observed response and runs that outcome's `branches` steps.

A passing fixture establishes conformance, not merely one client's observed
behavior: every outcome listed in a step's `expect` — model-filled or
hand-authored — must be spec-permitted at that point in the DAG. Where the
specification is genuinely ambiguous, an outcome may be marked `disputed`
with a citation; a real spec violation by a client under test must not be
added to `expect` as a second legal alternative just because that client
currently exhibits it, since doing so would stop the fixture from ever
failing against that behavior.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`HiveFixture`](#hivefixture) test object, with the key string representing the test name.

## Consumption

For each [`HiveFixture`](#hivefixture) test object in the JSON fixture file, perform the following steps:

1. Start the client under test using:

    - [`network`](#-network-fork) to configure the execution fork schedule according to the [`Fork`](./common_types.md#fork) type definition.
    - [`pre`](#-pre-alloc) as the starting state allocation of the execution environment for the test.
    - [`genesisBlockHeader`](#-genesisblockheader-fixtureheader) as the genesis block header.
    - `HIVE_ENGINE_MAX_REORG_DEPTH`, derived from [`minReorgDepth`](#-minreorgdepth-optionalnumber), if present.

2. Send an initial `engine_forkchoiceUpdatedVX` to the genesis block and verify it returns `VALID`; verify the client's genesis block hash via `eth_getBlockByNumber(0)`.

3. Run [`steps`](#-steps-liststep) in order. For each step:

    1. Resolve every label referenced by the step to a hash (or to the label itself, for a client-built payload not yet bound).
    2. Send the request (or perform the RPC observation).
    3. Select the first entry of the step's `expect` list whose constraints match the observed response; fail the test if none match.
    4. Run the steps listed in `branches` under the matched outcome's `id`, if any (recursively).

## Structures

### `HiveFixture`

#### - `network`: [`Fork`](./common_types.md#fork)

Fork configuration for the test. It is guaranteed that this field contains the same value as `config.network`.

#### - `config`: [`FixtureConfig`](./blockchain_test_engine.md#fixtureconfig)

Chain configuration object to be applied to every client running the test.

#### - `genesisBlockHeader`: [`FixtureHeader`](./blockchain_test.md#fixtureheader)

Genesis block header.

#### - `pre`: [`Alloc`](./common_types.md#alloc-mappingaddressaccount)

Starting account allocation for the test. State root calculated from this allocation must match the one in the genesis block.

#### - `blocks`: [`Mapping`](./common_types.md#mapping)`[String,`[`FixtureReorgBlock`](#fixturereorgblock)`]`

The block DAG, keyed by label.

#### - `steps`: [`List`](./common_types.md#list)`[`[`Step`](#step)`]`

Ordered, branching script of Engine API / JSON-RPC steps.

#### - `minReorgDepth`: [`Optional`](./common_types.md#optional)`[`[`Number`](./common_types.md#number)`]`

Minimum side-chain reorg depth (in blocks) the client must apply without refusing for capacity reasons; the consumer sets the client's cap (`HIVE_ENGINE_MAX_REORG_DEPTH`) to it. `None` keeps client defaults.

#### - `meta`: [`Mapping`](./common_types.md#mapping)`[String,``Any``]`

Free-form metadata about the test (e.g. `class`,`reorgDepth`) for offline analysis; not consumed by the runner. A `reorgDepth` of `1` (e.g. `test_sibling_reorg`) states a suite requirement — every client must handle a same-height sibling reorg — not a floor inferred from `minReorgDepth` or any client's observed capability.

### `FixtureReorgBlock`

#### - `parent`: `String`

Label of the parent block (`"genesis"` for a block extending the genesis block).

#### - `payload`: `FixtureNewPayloadRequest`

The block's `engine_newPayloadVX` request: `params` (version-dependent parameter tuple, see [`FixtureEngineNewPayload`](./blockchain_test_engine.md#fixtureenginenewpayload)) and `newPayloadVersion`. Response expectations live on the steps that send this block, not on the stored block itself.

### `Step`

A step is one of the variants below, distinguished by its `type` field. Every variant shares:

#### - `type`: `String`

One of `newPayload`,`forkchoiceUpdated`,`getPayload`,`assertHead`,`assertCanonical`,`assertState`,`assertReceipt`,`assertLogs`,`sendRawTransaction`,`assertTxStatus`.

#### - `description`: [`Optional`](./common_types.md#optional)`[String]`

Human-readable description of the step, for logging.

#### `newPayload`

- `block`: `String` — label of the block (or a `getPayload`-bound label) to send via `engine_newPayloadVX`.
- `expect`: [`List`](./common_types.md#list)`[`[`Outcome`](#outcome)`]` — legal outcomes.
- `branches`: [`Mapping`](./common_types.md#mapping)`[String,`[`List`](./common_types.md#list)`[`[`Step`](#step)`]]` — follow-up steps per matched outcome id.

#### `forkchoiceUpdated`

- `head` / `safe` / `finalized`: `String` — labels; `safe`/`finalized` default to `"zero"`.
- `version`: [`Number`](./common_types.md#number) — `engine_forkchoiceUpdatedVX` version; when unset, that of the payload attributes' fork for a build request, else of the head block's fork.
- `payloadAttributes`: [`Optional`](./common_types.md#optional)`[`[`PayloadAttributes`](#payloadattributes)`]` — if set, a payload build is requested.
- `expect` / `branches`: as above.

#### `getPayload`

- `bind`: `String` — new label for the built payload.
- `version`: [`Number`](./common_types.md#number) — `engine_getPayloadVX` version.
- `parent`: `String` — expected parent of the built payload.
- `transactionsInclude` / `transactionsExclude`: [`List`](./common_types.md#list)`[`[`TxRef`](#txref)`]` — transactions that must (or must not) be in the built payload.

The wait before `engine_getPayloadVX` is the consumer's `--get-payload-wait-time` option, not a fixture field.

#### `assertHead`

- `latest` / `safe` / `finalized`: [`Optional`](./common_types.md#optional)`[String]` — expected labels, checked via `eth_getBlockByNumber`.

#### `assertCanonical`

- `blocks`: [`Mapping`](./common_types.md#mapping)`[`[`HexNumber`](./common_types.md#hexnumber)`,`[`Optional`](./common_types.md#optional)`[String]]` — expected label (or `None` for "no block") at each height.

#### `assertState`

- `at`: `String` — block label or `"genesis"` (that block's own state; it must be canonical when the step runs), or `"latest"`. Default `"latest"`.
- `accounts`: [`Mapping`](./common_types.md#mapping)`[`[`Address`](./common_types.md#address)`,`[`AccountExpectation`](#accountexpectation)`]`.

#### `assertReceipt`

- `tx`: [`TxRef`](#txref).
- `block`: [`Optional`](./common_types.md#optional)`[String]` — expected receipt block label, or `None` for no receipt.
- `status`: [`Optional`](./common_types.md#optional)`[`[`HexNumber`](./common_types.md#hexnumber)`]`.

#### `assertLogs`

- `address`: [`Optional`](./common_types.md#optional)`[`[`Address`](./common_types.md#address)`]`.
- `fromBlock` / `toBlock`: [`HexNumber`](./common_types.md#hexnumber)`|String` — defaults `"earliest"` / `"latest"`.
- `blocks`: [`List`](./common_types.md#list)`[String]` — labels whose logs must appear, one entry per expected log.

#### `sendRawTransaction`

- `tx`: [`TxRef`](#txref).
- `expect`: [`List`](./common_types.md#list)`[String]` — subset of `["accepted", "rejected"]`; default `["accepted"]`.

#### `assertTxStatus`

- `tx`: [`TxRef`](#txref).
- `expect`: [`List`](./common_types.md#list)`[String]` — subset of `["included", "pending", "dropped"]`.
- `includedIn`: [`Optional`](./common_types.md#optional)`[String]` — required block label when `included` matches.

### `Outcome`

One legal outcome of an Engine API step. Every set field is a constraint; unset fields are not checked.

#### - `id`: `String`

Identifier; selects the `branches` entry to run when matched.

#### - `disputed`: [`Optional`](./common_types.md#optional)`[String]`

If set, the specification is ambiguous about this outcome; the value is a reference (e.g. an issue URL). A disputed outcome still passes.

#### - `status`: [`Optional`](./common_types.md#optional)`[String]`

Expected `payloadStatus.status` (`VALID`,`INVALID`,`SYNCING`,`ACCEPTED`,`INVALID_BLOCK_HASH`).

#### - `latestValidHash`: [`Optional`](./common_types.md#optional)`[String]`

Expected `latestValidHash` as a block label, `"null"`, or `"any"`.

#### - `errorCode`: [`Optional`](./common_types.md#optional)`[`[`Number`](./common_types.md#number)`]`

Expected JSON-RPC error code (e.g. `-38002`,`-38006`).

#### - `anyError`: [`Optional`](./common_types.md#optional)`[``Bool``]`

If `true`, any JSON-RPC error matches (for uncoded errors).

#### - `headMoved`: [`Optional`](./common_types.md#optional)`[``Bool``]`

`forkchoiceUpdated` only: whether `latest` equals the requested head right after the call. Distinguishes an applied update from a no-op when both answer `VALID` with the same `latestValidHash`.

#### - `validationError`: [`Optional`](./common_types.md#optional)`[String]`

`"required"` or `"none"`: whether `validationError` must be present or absent.

#### - `payloadId`: [`Optional`](./common_types.md#optional)`[String]`

`"nonNull"` or `"null"`, for a `forkchoiceUpdated` with payload attributes.

### `PayloadAttributes`

Payload attributes sent with `forkchoiceUpdated` to start a build; fields match the Engine API's `PayloadAttributesVX`, including Amsterdam's `slotNumber` and `targetGasLimit`.

### `AccountExpectation`

#### - `balance` / `nonce`: [`Optional`](./common_types.md#optional)`[`[`HexNumber`](./common_types.md#hexnumber)`]`

#### - `storage`: [`Optional`](./common_types.md#optional)`[`[`Mapping`](./common_types.md#mapping)`[`[`Hash`](./common_types.md#hash)`,`[`Hash`](./common_types.md#hash)`]]`

### `TxRef`

Reference to a transaction of a fixture block.

#### - `block`: `String`

#### - `index`: [`Number`](./common_types.md#number)

Default `0`.

## Differences from Blockchain Engine Tests

1. **Block DAG, not a list**: blocks name their parent by label, so side chains, invalid-block descendants and re-convergence are first-class.
2. **Branching step script**: `steps` is not a flat payload list; a step's `expect` can list several spec-legal outcomes and `branches` continues down the outcome that was actually observed.
3. **Explicit forkchoice state**: `forkchoiceUpdated` steps set `head`/`safe`/`finalized` independently instead of always following the last payload.
4. **Client-built payloads**: `getPayload` retrieves and binds a payload the client built itself, which can then be delivered back via `newPayload`.
5. **State observations**: `assertState`/`assertReceipt`/`assertLogs`/`assertTxStatus` steps check observable RPC state after a forkchoice update, instead of a single fixture-wide `post` allocation.

## Fork Support

Blockchain Engine Reorg Tests are only supported for post-merge forks (Paris and later), as they rely entirely on the Engine API.
