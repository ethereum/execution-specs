# Blockchain Engine Reorg Tests  <!-- markdownlint-disable MD051 (MD051=link-fragments "Link fragments should be valid") -->

The Blockchain Engine Reorg Test fixture format tests are included in the fixtures subdirectory `blockchain_tests_engine_reorg`, and describe a DAG of Engine API payloads plus a branching script of Engine API / JSON-RPC steps to verify chain reorganization behavior.

These are produced by the `ReorgTest` test spec.

## Description

Unlike [`BlockchainEngineFixture`](./blockchain_test_engine.md) (a linear payload list where the consumer always sends `forkchoiceUpdated(head=payload)` after each payload), this format lets a test describe side chains, explicit forkchoice states (head, safe, finalized), multiple legal outcomes per step, outcome-specific follow-up steps (branches), client-built payloads (`getPayload` binds the built payload to a new label), transaction-pool observations, and a second client for sync-delivered reorgs.

Every block in the DAG names its parent by label instead of relying on list order, so sibling blocks and blocks built on top of an invalid block are first-class. Every hash-valued step field is a label (`"genesis"` is reserved for the genesis block, `"zero"` for the zero hash; labels introduced by `getPayload.bind` are resolved at run time); the consumer resolves labels to hashes itself, so fixtures are byte-identical across clients.

Each step's `expect` field is a list of legal outcomes (the [Engine API reference model](../../library/execution_testing_specs.md#execution_testing.specs.engine_model) fills it in at fill time for any step an author left unannotated, deriving the outcomes the [execution-apis](https://github.com/ethereum/execution-apis) specification allows a conformant client to return); the consumer selects the first outcome matching the observed response and runs that outcome's `branches` steps.

A single JSON fixture file is composed of a JSON object where each key-value pair is a different [`HiveFixture`](#hivefixture) test object, with the key string representing the test name.

## Consumption

For each [`HiveFixture`](#hivefixture) test object in the JSON fixture file, perform the following steps:

1. Start the main client using:

    - [`network`](#-network-fork) to configure the execution fork schedule according to the [`Fork`](./common_types.md#fork) type definition.
    - [`pre`](#-pre-alloc) as the starting state allocation of the execution environment for the test.
    - [`genesisBlockHeader`](#-genesisblockheader-fixtureheader) as the genesis block header.
    - The client environment's `HIVE_*` variables from [`requires`](#-requires-optionalmappingstringstring), if present.

2. If [`clients`](#-clients-mappingstringfixtureclient) is non-empty, start one additional client per entry, of the same client type as the main client, peered with it via `admin_addPeer`.

3. Send an initial `engine_forkchoiceUpdatedVX` to the genesis block on every client and verify each returns `VALID`; verify each client's genesis block hash via `eth_getBlockByNumber(0)`.

4. Run [`steps`](#-steps-liststep) in order. For each step:

    1. Resolve every label referenced by the step to a hash (or to the label itself, for a client-built payload not yet bound).
    2. Send the request (or perform the RPC observation) against the client named by the step's `on` field (`"main"` by default).
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

#### - `blocks`: [`Mapping`](./common_types.md#mapping)`[`[`String`](./common_types.md#string)`, `[`FixtureReorgBlock`](#fixturereorgblock)`]`

The block DAG, keyed by label.

#### - `steps`: [`List`](./common_types.md#list)`[`[`Step`](#step)`]`

Ordered, branching script of Engine API / JSON-RPC steps.

#### - `clients`: [`Mapping`](./common_types.md#mapping)`[`[`String`](./common_types.md#string)`, `[`FixtureClient`](#fixtureclient)`]`

Additional clients besides `main`, keyed by the name used in a step's `on` field. Empty when the test only exercises a single client.

#### - `requires`: [`Optional`](./common_types.md#optional)`[`[`Mapping`](./common_types.md#mapping)`[`[`String`](./common_types.md#string)`, `[`String`](./common_types.md#string)`]]`

Client environment (`HIVE_*`) variables the consumer applies at client start, e.g. a client-specific reorg-depth cap. `None` means client defaults.

#### - `meta`: [`Mapping`](./common_types.md#mapping)`[`[`String`](./common_types.md#string)`, `[`Any`](./common_types.md#any)`]`

Free-form metadata about the test (e.g. `class`, `reorgDepth`) for offline analysis; not consumed by the runner.

### `FixtureReorgBlock`

#### - `parent`: [`String`](./common_types.md#string)

Label of the parent block (`"genesis"` for a block extending the genesis block).

#### - `payload`: [`FixtureEngineNewPayload`](./blockchain_test_engine.md#fixtureenginenewpayload)

The block's `engine_newPayloadVX` directive.

### `FixtureClient`

#### - `description`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

Human-readable description of the client's role in the test.

### `Step`

A step is one of the variants below, distinguished by its `type` field. Every variant shares:

#### - `type`: [`String`](./common_types.md#string)

One of `newPayload`, `forkchoiceUpdated`, `getPayload`, `assertHead`, `waitForHead`, `assertCanonical`, `assertState`, `assertReceipt`, `assertLogs`, `sendRawTransaction`, `assertTxStatus`.

#### - `on`: [`String`](./common_types.md#string)

Name of the client the step is executed on; `"main"` unless the step targets one of `clients`.

#### - `description`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

Human-readable description of the step, for logging.

#### `newPayload`

- `block`: [`String`](./common_types.md#string) — label of the block (or a `getPayload`-bound label) to send via `engine_newPayloadVX`.
- `expect`: [`List`](./common_types.md#list)`[`[`Outcome`](#outcome)`]` — legal outcomes.
- `branches`: [`Mapping`](./common_types.md#mapping)`[`[`String`](./common_types.md#string)`, `[`List`](./common_types.md#list)`[`[`Step`](#step)`]]` — follow-up steps per matched outcome id.

#### `forkchoiceUpdated`

- `head` / `safe` / `finalized`: [`String`](./common_types.md#string) — labels; `safe`/`finalized` default to `"zero"`.
- `version`: [`Number`](./common_types.md#number) — `engine_forkchoiceUpdatedVX` version; derived from the head block's fork when unset.
- `payloadAttributes`: [`Optional`](./common_types.md#optional)`[`[`FixturePayloadAttributes`](#fixturepayloadattributes)`]` — if set, a payload build is requested.
- `expect` / `branches`: as above.

#### `getPayload`

- `bind`: [`String`](./common_types.md#string) — new label for the built payload.
- `version`: [`Number`](./common_types.md#number) — `engine_getPayloadVX` version.
- `delay`: [`Number`](./common_types.md#number) — seconds to wait after the build request before retrieving; default `1.0`.
- `parent`: [`String`](./common_types.md#string) — expected parent of the built payload.
- `transactionsInclude` / `transactionsExclude`: [`List`](./common_types.md#list)`[`[`TxRef`](#txref)`]` — transactions that must (or must not) be in the built payload.

#### `assertHead`

- `latest` / `safe` / `finalized`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]` — expected labels, checked via `eth_getBlockByNumber`.

#### `waitForHead`

- `latest`: [`String`](./common_types.md#string) — label to poll `eth_getBlockByNumber("latest")` for.
- `timeout`: [`Number`](./common_types.md#number) — seconds; default `60`.

#### `assertCanonical`

- `blocks`: [`Mapping`](./common_types.md#mapping)`[`[`HexNumber`](./common_types.md#hexnumber)`, `[`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]]` — expected label (or `None` for "no block") at each height.

#### `assertState`

- `at`: [`String`](./common_types.md#string) — block label, or `"latest"`.
- `accounts`: [`Mapping`](./common_types.md#mapping)`[`[`Address`](./common_types.md#address)`, `[`AccountExpectation`](#accountexpectation)`]`.

#### `assertReceipt`

- `tx`: [`TxRef`](#txref).
- `block`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]` — expected receipt block label, or `None` for no receipt.
- `status`: [`Optional`](./common_types.md#optional)`[`[`HexNumber`](./common_types.md#hexnumber)`]`.

#### `assertLogs`

- `address`: [`Optional`](./common_types.md#optional)`[`[`Address`](./common_types.md#address)`]`.
- `fromBlock` / `toBlock`: [`HexNumber`](./common_types.md#hexnumber)` | `[`String`](./common_types.md#string) — defaults `"earliest"` / `"latest"`.
- `blocks`: [`List`](./common_types.md#list)`[`[`String`](./common_types.md#string)`]` — labels whose logs must appear, one entry per expected log.

#### `sendRawTransaction`

- `tx`: [`TxRef`](#txref).
- `expect`: [`List`](./common_types.md#list)`[`[`String`](./common_types.md#string)`]` — subset of `["accepted", "rejected"]`; default `["accepted"]`.

#### `assertTxStatus`

- `tx`: [`TxRef`](#txref).
- `expect`: [`List`](./common_types.md#list)`[`[`String`](./common_types.md#string)`]` — subset of `["included", "pending", "dropped"]`.
- `includedIn`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]` — required block label when `included` matches.

### `Outcome`

One legal outcome of an Engine API step. Every set field is a constraint; unset fields are not checked.

#### - `id`: [`String`](./common_types.md#string)

Identifier; selects the `branches` entry to run when matched.

#### - `disputed`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

If set, the specification is ambiguous about this outcome; the value is a reference (e.g. an issue URL). A disputed outcome still passes.

#### - `status`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

Expected `payloadStatus.status` (`VALID`, `INVALID`, `SYNCING`, `ACCEPTED`).

#### - `latestValidHash`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

Expected `latestValidHash` as a block label, `"null"`, or `"any"`.

#### - `errorCode`: [`Optional`](./common_types.md#optional)`[`[`Number`](./common_types.md#number)`]`

Expected JSON-RPC error code (e.g. `-38002`, `-38006`).

#### - `anyError`: [`Optional`](./common_types.md#optional)`[`[`Bool`](./common_types.md#bool)`]`

If `true`, any JSON-RPC error matches (for uncoded errors).

#### - `headMoved`: [`Optional`](./common_types.md#optional)`[`[`Bool`](./common_types.md#bool)`]`

`forkchoiceUpdated` only: whether `latest` equals the requested head right after the call. Distinguishes an applied update from a no-op when both answer `VALID` with the same `latestValidHash`.

#### - `validationError`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

`"required"` or `"none"`: whether `validationError` must be present or absent.

#### - `payloadId`: [`Optional`](./common_types.md#optional)`[`[`String`](./common_types.md#string)`]`

`"nonNull"` or `"null"`, for a `forkchoiceUpdated` with payload attributes.

### `FixturePayloadAttributes`

Payload attributes sent with `forkchoiceUpdated` to start a build; fields match the Engine API's `PayloadAttributesVX`.

### `AccountExpectation`

#### - `balance` / `nonce`: [`Optional`](./common_types.md#optional)`[`[`HexNumber`](./common_types.md#hexnumber)`]`

#### - `storage`: [`Optional`](./common_types.md#optional)`[`[`Mapping`](./common_types.md#mapping)`[`[`Hash`](./common_types.md#hash)`, `[`Hash`](./common_types.md#hash)`]]`

### `TxRef`

Reference to a transaction of a fixture block.

#### - `block`: [`String`](./common_types.md#string)

#### - `index`: [`Number`](./common_types.md#number)

Default `0`.

## Differences from Blockchain Engine Tests

1. **Block DAG, not a list**: blocks name their parent by label, so side chains, invalid-block descendants and re-convergence are first-class.
2. **Branching step script**: `steps` is not a flat payload list; a step's `expect` can list several spec-legal outcomes and `branches` continues down the outcome that was actually observed.
3. **Explicit forkchoice state**: `forkchoiceUpdated` steps set `head`/`safe`/`finalized` independently instead of always following the last payload.
4. **Client-built payloads**: `getPayload` retrieves and binds a payload the client built itself, which can then be delivered back via `newPayload`.
5. **Multiple clients**: `clients` lets a test start additional, peered clients and target steps at them via `on`, to cover reorgs delivered by sync rather than direct submission.
6. **State observations**: `assertState`/`assertReceipt`/`assertLogs`/`assertTxStatus` steps check observable RPC state after a forkchoice update, instead of a single fixture-wide `post` allocation.

## Fork Support

Blockchain Engine Reorg Tests are only supported for post-merge forks (Paris and later), as they rely entirely on the Engine API.
