# Client Test Runners

One interface for clients' `blocktest`, `enginetest` and `buildtest` runners, so any harness can run any client the same way and read the same results.

MUST, SHOULD and MAY are as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Commands

- `blocktest` runs [Blockchain Tests](../test_formats/blockchain_test.md): each block is imported as the client's sync would import it.
- `enginetest` runs [Blockchain Engine Tests](../test_formats/blockchain_test_engine.md): each payload goes through the client's Engine API handler.
- `buildtest` runs [Blockchain Engine Tests](../test_formats/blockchain_test_engine.md) through the client's block builder: for each payload expected to be valid, the client builds a block from the payload's parent, attributes and transactions, and the runner compares it with the payload (see [Build tests use the client's own builder](#build-tests-use-the-clients-own-builder)).

All three MUST take any number of fixture paths, files or directories mixed, and run all of them in one process with one set of results, so a large fixture set pays the client's startup once. A path that does not exist or cannot be read, whether named or found inside a directory, MUST be reported on stderr with exit code `2` before any fixture runs, so a typo never silently drops fixtures.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Every fixture ran and passed. |
| `1` | Every fixture ran, and at least one failed. |
| `2` | The runner could not run every fixture: a path that does not exist or cannot be read (reported before any fixture runs), or a fixture file it cannot parse (reported on stderr, never in the results; the other files still run and are reported). |

A harness trusts the [results](#results) only after `0` or `1`; any other code, a crash's included, means results may be missing. A runner whose CI relies on exit `0` for failing fixtures MAY keep it, as [Clients](#clients) lists, since `pass` still carries every verdict; it MUST still exit `2` in the cases above.

## Flags

Runners MUST support every flag below that the Runner column names for them, spelled as shown. `--version` is answered by the binary itself.

| Flag | Runner | What it does | Why it matters for testing |
|---|---|---|---|
| `--version` | the binary | Prints one line naming the tool and its version, then exits 0. | A harness records exactly which build produced a result. |
| `--workers N` | all three | Runs fixtures on `N` workers in one process; results do not depend on `N`. | Large fixture sets finish in reasonable time. |
| `--bal-sequential` | `blocktest`, `enginetest` | Runs every block on the client's sequential executor instead of its block-level access list (BAL) parallel executor. | The same fixtures check both executors against the same expectations. |
| `--bal-withhold` | `blocktest` | Executes every block without using the fixture's access list. | Tests the path a node takes for a block received without a list, where it must build the list itself. |
| `--bal-report` | `blocktest`, `enginetest` | Prints which executor ran each block, and any sequential fallback, on stderr (see [Execution report](#execution-report)). | Shows a run exercised the path it meant to, instead of silently falling back. |

By default, blocks from Amsterdam on that have an access list run on the client's parallel executor, as on a node, wherever the client's code path has one.

## Results

stdout MUST carry only the results: a JSON array with one object per fixture. Everything else goes to stderr. Each client keeps its own switch for JSON output (see [Clients](#clients)).

```json
[{"name": "tests/amsterdam/eip7928_block_level_access_lists/test_x.py::test_y[fork_Amsterdam-blockchain_test]", "pass": true, "rejections": [{"index": 1, "hash": "0x…", "error": "<client error>"}]}]
```

[JSON schema of the results](client_runner_schemas.md#results)

- `name` is the fixture's key in the fixture file, verbatim. Short names repeat across modules, so a harness looks results up by the full ID.
- `pass` is true when the fixture's expected outcome (valid, or rejected) was met, whatever the reason given.
- `rejections` has one entry per block or payload the client rejected, in fixture order, and is `[]` when none was.
    - `index` is the position in the fixture's `blocks` or `engineNewPayloads`, from 0.
    - `hash` is the rejected block's hash, when the client computed one.
    - `error` is the client's own message, untranslated. For a JSON-RPC error it is `"<code>: <message>"`, plus `": <data>"` when the error carries data (a string as is, anything else as compact JSON). For a block that fails to decode, it is the decoder's message.

`buildtest` results also carry two keys ([JSON schema](client_runner_schemas.md#build-test-results)):

- `built` is the number of payloads the client built. A fixture whose payloads are all expected to be invalid builds none and passes, so a harness can tell it from one that was checked.
- `mismatches` has one entry per field of a fixture's payload in which the built payload differs, in fixture order, and is `[]` when none does.
    - `index` is the payload's position in `engineNewPayloads`, from 0.
    - `field` is the field's name as in the payload JSON, such as `stateRoot`, or `executionRequests`.
    - `expected` is the fixture's value and `got` the built one, both as they appear in the payload JSON.

Clients MAY add keys to a result, such as `fork`, and consumers ignore keys they do not know.

A runner MUST NOT map errors to exception names or compare them with the fixture's expected exception. The consumer checks reasons through the client's [exception mapper](exceptions.md). An engine runner MAY compare a JSON-RPC error's code with the payload's `errorCode`, since that code belongs to the Engine API, not to the client.

## Block tests deliver the access list

`blocktest` MUST deliver the access list of each block from Amsterdam on with the block (`blockAccessList`, or `rlp_decoded.blockAccessList` for an expected-invalid block), as the client's sync delivers a list received from a peer. Without it, block tests never reach the parallel executor a node runs for a block received with its list.

The runner hashes the list as delivered, its RLP in the order given, and compares that with the header's `blockAccessListHash`:

- On a match, it MUST attach the list, even if the client then finds it malformed: the header commits to it, so the block is judged with it.
- On a mismatch, or a list that cannot be encoded, it MUST drop the list. The block executes without one, and its verdict follows its header.

Under `--bal-withhold`, execution MUST NOT use the list: the runner either does not deliver it, or delivers it with the client's execution set to ignore it. Either way the client builds the list itself and checks it against the header, so the verdict is the same; only the client's error can differ.

## Engine tests use the client's own handler

`enginetest` MUST call the client's own Engine API handler, the code serving `engine_newPayloadV<n>` and `engine_forkchoiceUpdatedV<n>`, at the versions the fixture names, with params decoded by the client's own decoder. The client's real version checks, payload validator and execution MUST run; nothing is re-implemented or mocked in their place. Engine-only bugs live in that code (a method version that accepts the wrong fork, a payload field decoded wrongly), and a mock would skip them.

Call the handler in-process, directly or through the client's RPC method dispatch: a server, transport or node per fixture makes large runs too slow.

## Build tests use the client's own builder

`buildtest` MUST call the client's own block builder, the code serving [`testing_buildBlockV1`](https://github.com/ethereum/execution-apis/blob/main/src/testing/testing_buildBlockV1.yaml), in-process, as `enginetest` calls the Engine API handler. The client's real transaction application, header derivation, system calls, withdrawals, requests and access list construction MUST run, and nothing is re-implemented or mocked in their place. Builder-only bugs live in that code (a system call made in another order than on import, a request or access list derived wrongly), and `blocktest` and `enginetest` never reach it, since they only import blocks.

For each fixture, starting from its genesis, the runner takes the payloads in `engineNewPayloads` in order:

1. A payload with a `validationError` or an `errorCode` is skipped: it is neither built nor imported, since no later payload builds on it.
2. Any other payload is built on its `parentHash`, with:
    - the payload's `timestamp`, `prevRandao` and `feeRecipient` (as `suggestedFeeRecipient`), its `withdrawals` from Shanghai on, its `parentBeaconBlockRoot` param from Cancun on, and its `slotNumber` from Amsterdam on,
    - the payload's `transactions`, in order and as the payload carries them, so a blob transaction comes without its blobs, and its `extraData`. The block needs only each transaction's versioned hashes, so the runner MUST have the builder build it anyway. A client whose `testing_buildBlockV1` requires the blobs MAY keep that and turn it off for the runner only,
    - the payload's `gasLimit` as the builder's target: `targetGasLimit` from Amsterdam on, and the builder's own gas target setting before. A valid payload's gas limit is always within one step of its parent's, so the built gas limit MUST equal it.
3. Every field of the fixture's execution payload is compared with the built one's, `gasLimit` and `blockHash` included, and from Prague on the payload's `executionRequests` with the built ones. Each difference is one of the result's `mismatches`. A field only the built payload has is not compared, since `testing_buildBlockV1` returns an `ExecutionPayloadV3` for any block before Amsterdam, so a block before Cancun comes back with Cancun's fields. The block hash already covers the header the client built. The blobs bundle is not compared, since the fixture does not carry one.
4. The fixture's payload, not the built one, is then imported through the client's Engine API handler, as `enginetest` imports it, so the chain follows the fixture even after a mismatch. Building MUST NOT move the client's head, as `testing_buildBlockV1` requires.

A fixture passes when every payload it builds has no mismatch and imports as valid. A payload the client refuses to build or to import is one of the result's `rejections`, with the client's own error, and fails the fixture. A payload refused at both steps has an entry for each, the build's first. After a refused build the runner still imports the payload, so later payloads are still built. After a refused import it stops the fixture, since the client no longer has the parent of the next payload.

```json
[{"name": "tests/prague/eip7002_el_triggerable_withdrawals/test_x.py::test_y[fork_Prague-blockchain_test_engine]", "pass": false, "rejections": [], "built": 2, "mismatches": [{"index": 1, "field": "stateRoot", "expected": "0x…", "got": "0x…"}]}]
```

The BAL flags do not apply to `buildtest`: the client derives each access list itself while building.

The [`build-block`](../running.md#block-building) simulator runs the same checks over hive, against a running client's `testing_buildBlockV1`. A runner checks in-process and sets the gas limit target, so it also compares `gasLimit` and `blockHash`, which the simulator only checks against the allowed range.

## Execution report

With `--bal-report`, `blocktest` and `enginetest` MUST print one single-line JSON object on stderr per executed block, at the point where the client chooses its executor:

```json
{"event": "balExecution", "block": 12, "hash": "0x…", "path": "sequential", "reason": "disabled"}
```

[JSON schema of a `balExecution` line](client_runner_schemas.md#bal-execution-lines)

`path` is the executor that ran the block, `parallel` or `sequential`, and `reason` says why:

| `reason` | When | `path` |
|---|---|---|
| `withheld` | `--bal-withhold` is set and the block has a list | any |
| `bad-access-list` | the runner dropped the block's delivered list | any |
| `disabled` | `--bal-sequential` | `sequential` |
| `no-access-list` | the block has no list | `sequential` |
| `pre-amsterdam` | the block's fork has no access lists | `sequential` |
| a lowercase client-specific name | another condition the client checks | `sequential` |
| empty | none of the above | `parallel` |

`withheld` and `bad-access-list` come first. Otherwise a `sequential` block gives the first condition, in the client's own order, that ruled parallel out.

A client that re-runs a block sequentially after its parallel executor fails MUST print one more line for that block, and no second `balExecution` line:

```json
{"event": "balFallback", "block": 12, "hash": "0x…", "parallelError": "…", "sequentialResult": "invalid", "sequentialError": "…"}
```

[JSON schema of a `balFallback` line](client_runner_schemas.md#bal-fallback-lines)

`sequentialResult` is `valid` or `invalid`, and `sequentialError` is empty when valid. The block's verdict stays the sequential one.

Genesis and blocks rejected before execution print nothing. Clients MAY add keys, and consumers ignore keys they do not know. Without the flag, stderr is unchanged. Under `--workers`, lines from different fixtures interleave, and `hash` ties each line to its block.

## Clients

| Client | Block tests | Engine tests | JSON results | Exit code when a fixture fails |
|---|---|---|---|---|
| go-ethereum | `evm blocktest` | `evm enginetest` | always | `1` |
| Besu | `evmtool block-test` | `evmtool engine-test --outcome-only` | `--json-array` | `1` |
| Nethermind | `nethtest blocktest` | `nethtest enginetest` | always | `0`, which its CI relies on |
| Erigon | `evm blocktest` | `evm enginetest` | `--jsonout` | `1` |
| Reth | `ef-test-runner blocktest` | `ef-test-runner enginetest` | always | `1` |
| ethrex | `blocktest` (package `ef_tests-runners`) | `enginetest` (package `ef_tests-runners`) | `--json` | `1` |
| Nimbus | `test_runner blocktest` | `test_runner enginetest` | always | `1` |

- Besu's `engine-test` checks a rejected payload's error against the fixture's expected exception by default, with or without `--json-array`, and `--outcome-only` turns that check off. Nethermind's `enginetest` is the other way around: it checks the reason only under `--match-exceptions`.
- Reth's block import has only a sequential executor, so its `blocktest` reports `sequential` with reason `block-import`.
- Erigon's `--bal-withhold` delivers the list and sets the same switch as its `IGNORE_BAL` environment variable, so execution ignores the list.
- No client in the table has a `buildtest` runner yet.
