# Client Test Runners

One interface for clients' `blocktest` and `enginetest` runners, so any harness can run any client the same way and read the same results.

MUST, SHOULD and MAY are as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Commands

- `blocktest` runs [Blockchain Tests](../test_formats/blockchain_test.md): each block is imported as the client's sync would import it.
- `enginetest` runs [Blockchain Engine Tests](../test_formats/blockchain_test_engine.md): each payload goes through the client's Engine API handler.

Both MUST take any number of fixture paths, files or directories mixed, and run all of them in one process with one set of results, so a large fixture set pays the client's startup once. A path that does not exist or cannot be read MUST be reported on stderr with a non-zero exit before any fixture runs, so a typo never silently drops fixtures.

A runner SHOULD exit non-zero when any fixture fails; [Clients](#clients) lists each client's exit code.

## Flags

Runners MUST support every flag below, spelled as shown; `--bal-withhold` applies to `blocktest` only.

| Flag | Runner | What it does | Why it matters for testing |
|---|---|---|---|
| `--version` | both | Prints one line naming the tool and its version, then exits 0. | A harness records exactly which build produced a result. |
| `--workers N` | both | Runs fixtures on `N` workers in one process; results do not depend on `N`. | Large fixture sets finish in reasonable time. |
| `--bal-sequential` | both | Runs every block on the client's sequential executor instead of its block-level access list (BAL) parallel executor. | The same fixtures check both executors against the same expectations. |
| `--bal-withhold` | `blocktest` | Executes every block without using the fixture's access list. | Tests the path a node takes for a block received without a list, where it must build the list itself. |
| `--bal-report` | both | Prints which executor ran each block, and any sequential fallback, on stderr (see [Execution report](#execution-report)). | Shows a run exercised the path it meant to, instead of silently falling back. |

By default, blocks from Amsterdam on that have an access list run on the client's parallel executor, as on a node, wherever the client's code path has one.

## Results

stdout MUST carry only the results: a JSON array with one object per fixture. Everything else goes to stderr. Each client keeps its own switch for JSON output (see [Clients](#clients)).

```json
[{"name": "tests/amsterdam/eip7928_block_level_access_lists/test_x.py::test_y[fork_Amsterdam-blockchain_test]", "pass": true, "rejections": [{"index": 1, "hash": "0x…", "error": "<client error>"}]}]
```

- `name` is the fixture's key in the fixture file, verbatim. Short names repeat across modules, so a harness looks results up by the full ID.
- `pass` is true when the fixture's expected outcome (valid, or rejected) was met, whatever the reason given.
- `rejections` has one entry per block or payload the client rejected, in fixture order, and is `[]` when none was.
    - `index` is the position in the fixture's `blocks` or `engineNewPayloads`, from 0.
    - `hash` is the rejected block's hash, when the client computed one.
    - `error` is the client's own message, untranslated. For a JSON-RPC error it is `"<code>: <message>"`, plus `": <data>"` when the error carries data (a string as is, anything else as compact JSON). For a block that fails to decode, it is the decoder's message.

Clients MAY add keys to a result, such as `fork`, and consumers ignore keys they do not know.

A runner MUST NOT map errors to exception names or compare them with the fixture's expected exception. The consumer checks reasons through the client's [exception mapper](exceptions.md), which keeps every client free of a copied table to sync.

## Block tests deliver the access list

`blocktest` MUST deliver the access list of each block from Amsterdam on with the block (`blockAccessList`, or `rlp_decoded.blockAccessList` for an expected-invalid block), as the client's sync delivers a list received from a peer. Without it, block tests never reach the parallel executor a node runs for a block received with its list.

The runner hashes the list as delivered, its RLP in the order given, and compares that with the header's `blockAccessListHash`:

- On a match, it MUST attach the list, even if the client then finds it malformed: the header commits to it, so the block is judged with it.
- On a mismatch, or a list that cannot be encoded, it MUST drop the list. The block executes without one, and its verdict follows its header.

Under `--bal-withhold`, execution MUST NOT use the list: the runner either does not deliver it, or delivers it with the client's execution set to ignore it. Either way the client builds the list itself and checks it against the header, so the verdict is the same; only the client's error can differ.

## Engine tests use the client's own handler

`enginetest` MUST call the client's own Engine API handler, the code serving `engine_newPayloadV<n>` and `engine_forkchoiceUpdatedV<n>`, at the versions the fixture names, with params decoded by the client's own decoder. The client's real version checks, payload validator and execution MUST run; nothing is re-implemented or mocked in their place. Engine-only bugs live in that code (a method version that accepts the wrong fork, a payload field decoded wrongly), and a mock would skip them.

Call the handler in-process, directly or through the client's RPC method dispatch: a server, transport or node per fixture makes large runs too slow.

## Execution report

With `--bal-report`, both runners MUST print one single-line JSON object on stderr per executed block, at the point where the client chooses its executor:

```json
{"event": "balExecution", "block": 12, "hash": "0x…", "path": "sequential", "reason": "disabled"}
```

`path` is the executor that ran the block, `parallel` or `sequential`, and `reason` says why:

| `reason` | When | `path` |
|---|---|---|
| `withheld` | `--bal-withhold` is set | any |
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

`sequentialResult` is `valid` or `invalid`, and `sequentialError` is empty when valid. The block's verdict stays the sequential one.

Genesis and blocks rejected before execution print nothing. Clients MAY add keys, and consumers ignore keys they do not know. Without the flag, stderr is unchanged. Under `--workers`, lines from different fixtures interleave, and `hash` ties each line to its block.

## Clients

The commands are being added to each client; the last column links each client's change until it merges.

| Client | Block tests | Engine tests | JSON results | Exit code on a failing fixture | Status |
|---|---|---|---|---|---|
| go-ethereum | `evm blocktest` | `evm enginetest` | always | non-zero | proposed <!-- LINK: geth PR --> |
| Besu | `evmtool block-test` | `evmtool engine-test` | `--json-array` | non-zero | proposed <!-- LINK: besu PR --> |
| Nethermind | `nethtest blocktest` | `nethtest enginetest` | always | 0, which its CI relies on | proposed <!-- LINK: nethermind PR --> |
| Erigon | `evm blocktest` | `evm enginetest` | `--jsonout` | 0, which its CI relies on | proposed <!-- LINK: erigon PR --> |
| Reth | `ef-test-runner blocktest` | `ef-test-runner enginetest` | always | non-zero | proposed <!-- LINK: reth PR --> |
| ethrex | `blocktest` (package `ef_tests-runners`) | `enginetest` (package `ef_tests-runners`) | `--json` | non-zero | proposed <!-- LINK: ethrex PR --> |

- Reth's block import has only a sequential executor, so its `blocktest` reports `sequential` with reason `block-import`.
- Erigon's `--bal-withhold` delivers the list and sets the switch its `IGNORE_BAL` environment variable sets, so execution ignores the list.

## Conformance checklist

- [ ] `--version` prints one line naming the tool and its version, and exits 0.
- [ ] A file and a directory in one call give one results array covering both.
- [ ] A missing path: an error on stderr, a non-zero exit, nothing run.
- [ ] A failing fixture gives the exit code listed in [Clients](#clients).
- [ ] Results are the same with `--workers 1` and `--workers 4`.
- [ ] Every result's `name` is its full fixture ID.
- [ ] A rejected block shows the client's raw error at the right `index`; a clean fixture shows `[]`.
- [ ] A block rejected for a different reason than expected still has `pass: true` (the consumer checks reasons through the exception mapper).
- [ ] `blocktest`: a list matching the header is attached, a mismatched list is dropped, and the verdict follows the header, with and without `--bal-sequential`.
- [ ] `enginetest` reaches the client's own handler in-process at the fixture's method versions.
- [ ] `enginetest`: a payload with a corrupted access list is INVALID, with and without `--bal-sequential`.
- [ ] `--bal-report` prints `parallel` lines by default (where the client's code path has a parallel executor), `sequential` with `disabled` under `--bal-sequential`, `withheld` under `--bal-withhold`, and `bad-access-list` on a dropped list; without the flag, stderr is unchanged.
