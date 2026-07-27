# Filling Tests for Features under Development

## Requirements

By default, the execution-testing framework only generates fixtures for forks that have been deployed to mainnet. In order to generate fixtures for evm features that are actively under development:

1. A version of the `evm` and `solc` tools that implement the feature must be available (although, typically only a developer version of the `evm` tool is required, usually the latest stable release of `solc` is adequate), and,
2. The development fork to test must be explicitly specified on the command-line:

    === "via the `--fork` flag"

          ```console
          uv run fill -k 4844 --fork=Cancun -v
          ```

    === "via the `--from` flag"

          ```console
          uv run fill -k 4844 --from=Cancun -v
          ```

    === "via the `--until` flag"

          ```console
          uv run fill -k 4844 --until=Cancun -v
          ```

!!! note "Specifying the `evm` binary via `evm-bin`"
     It is possible to explicitly specify the `evm` binary used to generate fixtures via the `--evm-bin` flag, for example,

     ```console
     uv run fill --fork=Cancun --evm-bin=/opt/bin/evm -v
     ```

## The Experimental `BinaryTree` Fork (EIP-8297)

`BinaryTree` is Amsterdam semantics with its state commitment replaced by the [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) Partitioned Binary Tree instead of the Merkle Patricia Trie. Like any fork under development it is registered `deployed=False`, so it is excluded from every default fill and from every `--until`/`--from` fork range; it is reached only by naming it explicitly with `--fork BinaryTree`.

### How to Fill It

`BinaryTree` cannot use the flags above the usual way, because two things collide: the `fill` recipe in the `Justfile` always appends `--until Amsterdam` to whatever arguments it's given, and the framework rejects `--fork` combined with `--from`/`--until` on the same invocation. `just fill --fork BinaryTree` therefore cannot work, so a dedicated `fill-binary-tree` recipe exists that is the same shape with `--until` simply omitted:

```console
just fill-binary-tree [paths]
```

A `paths` argument **replaces** the recipe's default instead of adding to it, and the default is `tests/binary_tree` — the dedicated EIP-8297 suite, not the whole repository. In practice that gives two distinct commands:

- `just fill-binary-tree` (no arguments) fills only `tests/binary_tree`. This is deliberately the fast, scoped run, since the full sweep below has an unmeasured runtime.
- `just fill-binary-tree tests` fills the *entire* `tests/` tree against `BinaryTree`, reinterpreting every other fork's tests through the binary tree. Use this form when porting the full suite.

The full-tree form is intentionally **not** wired into CI: it runs thousands of tests through a pure-Python tree implementation whose runtime has not been measured. This fork is not part of any CI fill sweep yet beyond the scoped suite (see the `omit` comment in `pyproject.toml`'s `[tool.coverage.run]` and the `ignore` entry in `.codecov.yaml`); CI only runs `just fill-binary-tree tests/binary_tree`.

### The Marker Trap When Porting Existing Tests

Filling the full `tests/` tree against `--fork BinaryTree` exercises every other fork's [validity markers](../writing_tests/test_markers.md) against a fork none of them were written with in mind. Verified against `packages/testing/src/execution_testing/cli/pytest_commands/plugins/forks/forks.py`:

- A test with **no validity marker at all**, or `valid_from(<any ancestor fork>)` (e.g. `Frontier`, `Shanghai`, `Amsterdam`), **does** select `BinaryTree`: it subclasses `Amsterdam`, so it satisfies an ordinary `>=` comparison against any ancestor fork and lands back in the selected set.
- `valid_until(...)` and `valid_before(...)` correctly **exclude** it, for the same subclass relationship compared the other way.
- `valid_at(...)` **excludes** it even for `valid_at("Amsterdam")`, because `valid_at` is an exact-set marker: it resolves its arguments to the literal named forks instead of comparing with `>=`/`<=`, and `BinaryTree` is never one of them unless spelled out explicitly. A handful of tests pinned with `valid_at` are therefore silently invisible to the port — collection succeeds and nothing warns, the tests just never run for this fork.

### Known Gaps

- **`valid_at`-pinned tests are excluded from the port** — see the marker trap above.
- **No MPT→PBT transition machinery.** The tree is populated from genesis; there is no `*ToBinaryTree` transition fork, so there is no `valid_at_transition_to` coverage for entering the binary tree mid-chain (`ethereum/state_pbt.py`'s module docstring states this explicitly).
- **Storage semantics are a placeholder for the eventual spec.** The provider treats a zero storage value as absence and drops a deleted account's storage outright, while EIP-8297's eventual access-event semantics never remove entries once written. This is a deliberate pure commitment-scheme swap, not an attempt at final semantics (`ethereum/state_pbt.py`).
- **Deleting an account diverges from the Merkle Patricia Trie provider**, visible through EIP-7610 (`account_has_storage` gates `CREATE2`): the MPT provider never pops a deleted account's storage trie, the binary tree provider does. Pinned by `tests/binary_trie/test_differential_mpt.py`; an open question for the spec, not a bug in either provider.
- **A balance of `2**128` or more has no protocol-level rejection.** It fails a raw `assert` inside `encode_basic_data` during state-root computation (`ethereum/binary_trie/embedding.py`) instead of invalidating the block through the normal exception path. Pinned by `tests/binary_trie/test_embedding.py::test_encode_basic_data_rejects_balance_past_sixteen_bytes`.
- **No client consumes these fixtures yet.** Engine-format fixtures fill without error, but no execution client implements EIP-8297, so nothing downstream of `fill` exercises them.

### Test Locations

!!! warning "`tests/binary_trie/` vs. `tests/binary_tree/` — easy to confuse"
     The two directory names differ by one letter and cover very different things:

     - `tests/binary_trie/` — plain Python unit tests of the tree, its embedding, and the `state_pbt` provider (including the differential tests against `state_mpt` above). No fixtures involved; run with `just binary-trie`.
     - `tests/binary_tree/` — the EEST suite: fork-aware tests that `fill` turns into JSON fixtures for `BinaryTree`. Run with `just fill-binary-tree`.

## Further Help

1. [`geth`/`evm` build documentation](https://geth.ethereum.org/docs/getting-started/installing-geth#build-from-source).
2. [`solc` build documentation](https://docs.soliditylang.org/en/v0.8.20/installing-solidity.html#building-from-source).

!!! note "Verifying `evm` and `solc` versions used"
     The versions used to generate fixtures are displayed in the console output:
     <figure markdown>  <!-- markdownlint-disable MD033 (MD033=no-inline-html) -->
          ![Screenshot of pytest test collection console output](./img/pytest_run_example.png){align=center}
     </figure>
