# Writing Specs

This page collects the style rules, cross-fork discipline, and CLI utilities you need when writing or modifying code under `src/ethereum/`.

The overarching goal is readability: anyone reading a fork from top to bottom should be able to follow what Ethereum does for a given block, without jumping between files or untangling abstractions. EELS deliberately prefers repeated code (WET: "write everything twice") over clever reuse (DRY), because duplication is easier to read than a network of abstractions.

## Style

### Spelling and naming

- Prefer descriptive English words (or *very common* abbreviations) in documentation and identifiers.
- Avoid EIP numbers in identifiers; prefer descriptive text (e.g. `FeeMarketTransaction` over `Eip1559Transaction`).
- Avoid uninformative prefixes in identifiers (like `get_` or `compute_`). They don't add useful meaning and take up valuable real estate.
- If a term is specific to the domain, there is a custom spell-check dictionary at `whitelist.txt`.

### Comments

- Don't repeat what is obvious from the code.
- Don't attribute semantic blocks to a specific EIP in a leading comment, because future EIPs can land between your first and last lines and silently inherit the attribution. Instead, describe the change in the function's docstring.

<details>
<summary><em>(expand)</em> Why EIP-attributed comments rot.</summary>

<br>Consider:
<table valign="top">

<tr valign="top">
<th>Fork T</th>
<th>Fork T+1</th>
</tr>

<tr valign="top">

<td>

<!-- Note that the trailing whitespace is necessary to move the copy button in the github UI over so it doesn't obscure the text. -->

```python
# EIP-1234: The dingus is the rate of fleep      
dingus = a + b
dingus += c ^ d
dingus /= fleep(e)
```

</td>

<td>

```python
# EIP-1234: The dingus is the rate of fleep      
dingus = a + b

# EIP-4567: Frobulate the dingus
dingus = frobulate(dingus)

dingus += c ^ d        # <-
dingus /= fleep(e)     # <-
```

</td>

</tr>

</table>

The marked lines (`<-`) are now incorrectly attributed to EIP-4567 in Fork+1. Instead, omit the EIP identifier in comments and describe changes introduced by the EIP in the function's docstring. The rendered diffs will make it pretty obvious what's changed.

</details>

### Docstrings

- Write in complete sentences, providing necessary background and context for the associated code.
- Function and method docstrings must use the imperative mood in the summary line.
    - **Good:** Build the house using the provided lumber.
    - **Bad:** Builds the house using the provided lumber.
- Always start with a single-line summary. When more detail is needed, use a multi-line docstring with a blank line after the summary line.
    - **One-line summary:**

      ```python
      """Return the pathname of the KOS root directory."""
      ```

    - **Multi-line:**

      ```python
      """
      Add a bloom entry to the bloom filter.

      The number of hash functions used is 3. They are calculated by
      taking the least significant 11 bits from the first 3 16-bit
      words of the `keccak_256()` hash of `bloom_entry`.
      """
      ```

- Format using markdown.
- Links to relevant standards and EIPs may be specified using reference-style links.

  ```python
  """
  Minimum gas cost per byte of calldata as per [EIP-7976].

  [EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
  """
  ```

- Avoid beginning docstrings with an article ("the"/"a") or a pronoun ("it", "they", etc.).
- Don't include the function's signature.

### Constants

- Do not include constant values in docstrings, neither as literals nor as expressions. It's too easy to change a constant's value and forget to update its docstring.
- Construct the constant's value from other constants or meaningful expressions in order to provide meaningful context.
    - **Great:** `TARGET_BLOB_GAS_PER_BLOCK = GAS_PER_BLOB * BLOB_SCHEDULE_TARGET`
        - Composed from named constants; the reader immediately understands what the value represents.
    - **Acceptable:** `TX_MAX_GAS = Uint(2 ** 24)`
        - More readable than a raw number, but still a literal expression that doesn't convey *why* this value was chosen.
    - **Bad:** `TX_MAX_GAS = Uint(16_777_216)`
        - A magic number with no context.

## Changes across multiple forks

Many contributions require changes across multiple forks, organized under `src/ethereum/forks/`. When making such changes, ensure that differences between the forks are minimal and consist only of necessary differences. This produces cleaner [diff outputs](https://ethereum.github.io/execution-specs/diffs/index.html).

When creating pull requests affecting multiple forks, we recommend submitting your PR in two steps:

1. Apply the changes on a single fork, open a *draft* pull request, and get feedback.
2. Apply the changes across the other forks, push them, and mark the pull request as ready for review.

This saves you having to apply code review feedback repeatedly for each fork.

## CLI utilities: `ethereum_spec_tools`

The repository ships with CLI utilities that help during spec development.

### New Fork Tool

This tool creates the base code for a new fork by copying the existing code from a given fork.

The command takes 4 arguments (2 optional):

- `from_fork`: The fork name from which the code is to be duplicated. Example: `"Tangerine Whistle"`.
- `to_fork`: The fork name of the new fork. Example: `"Spurious Dragon"`.
- `from_test` (optional): Name of the from-fork within the test fixtures in case it is different from fork name. Example: `"EIP150"`.
- `to_test` (optional): Name of the to-fork within the test fixtures in case it is different from the fork name. Example: `"EIP158"`.

For example, to create baseline code for `Spurious Dragon` from `Tangerine Whistle`:

```bash
uv run ethereum-spec-new-fork --from_fork="Tangerine Whistle" --to_fork="Spurious Dragon" --from_test=EIP150 --to_test=EIP158
```

The following must be updated manually afterwards:

1. The fork number and `MAINNET_FORK_BLOCK` in `__init__.py`. If you are proposing a new EIP, set `MAINNET_FORK_BLOCK` to `None`.
2. Any absolute package imports from other forks, e.g. in `trie.py`.
3. Package names under `setup.cfg`.
4. Add the new fork to the `monkey_patch()` function in `src/ethereum_optimized/__init__.py`.
5. Adjust the underline in `fork/__init__.py`.

### Sync Tool

The sync tool uses an RPC provider to fetch and validate blocks against EELS. The validated state can be stored in a local DB. Because syncing directly with the specs is very slow, the sync tool can also leverage the `ethereum_optimized` module, which contains alternative implementations of routines in EELS optimized for speed rather than clarity/readability.

Invoke the tool with `ethereum-spec-sync`. Arguments:

- `rpc-url`: Endpoint providing the Ethereum RPC API. Defaults to `http://localhost:8545/`.
- `unoptimized`: Don't use the optimized state/ethash (this can be extremely slow).
- `persist`: Store state in a database at this file path.
- `geth`: Use geth-specific RPC endpoints while fetching blocks.
- `reset`: Delete the database and start from scratch.
- `gas-per-commit`: Commit to database each time this much gas has been consumed. Defaults to `1_000_000_000`.
- `initial-state`: Start from the state in this database rather than genesis.
- `stop-at`: After syncing this block, exit successfully.

Option compatibility:

- The following options are *not* supported *with* `--unoptimized`: `--persist`, `--initial-state`, `--reset`.
- The following options are *not* supported *without* `--persist`: `--initial_state`, `--reset`.

### Patch Tool

This tool applies the unstaged changes in `SOURCE_FORK` to each of `TARGET_FORKS`. If some of the changes fail to apply, `.rej` files listing the unapplied hunks are left in the target fork.

Positional and flag arguments:

- Source fork (single value). For example: `frontier`.
- Target forks (one or more values). For example: `homestead`.
- `optimized`: Patch the optimized code instead.
- `tests`: Patch the tests instead.

Example: apply changes made in `Frontier` to `Homestead` and `Tangerine Whistle`:

```bash
uv run python src/ethereum_spec_tools/patch_tool.py frontier homestead tangerine_whistle
```

### Lint Tool

The spec lint tool checks for style and formatting issues specific to EELS and emits diagnostics when issues are found. Currently it verifies:

- The order of identifiers between each hardfork is consistent.
- Import statements follow the relevant import rules in modules.

Run it with `just lint-spec` (or `uv run ethereum-spec-lint`).

## Debugging with `--evm-trace`

A trace of the EVM execution for any test case can be obtained by passing the `--evm-trace` argument to pytest. Run it on a small number of tests at a time; the log can otherwise grow very large.

```bash
uv run pytest \
    'tests/json_loader/test_state_tests.py::test_state_tests_frontier[stAttackTest - ContractCreationSpam - 0]' \
    --evm_trace
```
