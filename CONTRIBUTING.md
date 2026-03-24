# Contribution Guidelines

Help is always welcome and there are plenty of options to contribute to the Ethereum Execution Layer Specifications (EELS).

In particular, we appreciate support in the following areas:

- Reporting issues
- Fixing and responding to [issues](https://github.com/ethereum/execution-specs/issues), especially those tagged as [E-easy](https://github.com/ethereum/execution-specs/labels/E-easy) which are meant as introductory issues for external contributors.
- Improving the documentation.

> [!IMPORTANT]
> Generally, we do not assign issues to external contributors. If you want to work on an issue, you are very welcome to go ahead and make a pull request. We would, however, be happy to answer questions you may have before you start implementing.

For details about EELS usage and building, please refer to the [README](https://github.com/ethereum/execution-specs/blob/master/README.md#usage)

## Contribution Guidelines

This specification aims to be:

1. **Correct** - Describe the _intended_ behavior of the Ethereum blockchain, and any deviation from that is a bug.
2. **Complete** - Capture the entirety of _consensus critical_ parts of Ethereum.
3. **Accessible** - Prioritize readability, clarity, and plain language over performance and brevity.

### Style

#### Spelling and Naming

- Attempt to use descriptive English words (or _very common_ abbreviations) in documentation and identifiers.
- Avoid using EIP numbers in identifiers, and prefer descriptive text instead (eg. `FeeMarketTransaction` instead of `Eip1559Transaction`).
- If necessary, there is a custom dictionary `whitelist.txt`.
- Avoid uninformative prefixes in identifiers (like `get_` or `compute_`). They don't add useful meaning and take up valuable real estate.

#### Comments

- Don't repeat what is obvious from the code.
- <details>
    <summary><em>(expand)</em> Consider how future changes will interleave with yours, especially when creating semantic blocks.</summary>

    <br>Consider:
    <table valign="top">

    <tr valign="top">
    <th>Fork T</th>
    <th>Fork T+1</th>
    </tr>

    <tr valign="top">

    <td>

    <!--
        Note that the trailing whitespace is necessary to move the copy button
        in the github UI over so it doesn't obscure the text.
    -->

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

    The marked lines (`<-`) are now incorrectly attributed to EIP-4567 in Fork+1. Instead, omit the EIP identifier in the comments, and describe the changes introduced by the EIP in the function's docstrings. The rendered diffs will make it pretty obvious what's changed.
  </details>

#### Docstrings

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

##### Constants

- Do not include constant values in docstrings, neither as literals nor as expressions. It's too easy to change a constant's value and forget to update its docstring.
- Construct the constant's value from other constants or meaningful expressions in order to provide meaningful context.
    - **Great:** `TARGET_BLOB_GAS_PER_BLOCK = GAS_PER_BLOB * BLOB_SCHEDULE_TARGET`
        - Composed from named constants; the reader immediately understands what the value represents.
    - **Acceptable:** `TX_MAX_GAS = Uint(2 ** 24)`
        - More readable than a raw number, but still a literal expression that doesn't convey _why_ this value was chosen.
    - **Bad:** `TX_MAX_GAS = Uint(16_777_216)`
        - A magic number with no context.

### Changes across various Forks

Many contributions require changes across multiple forks, organized under `src/ethereum/forks/*`. When making such changes, please ensure that differences between the forks are minimal and consist only of necessary differences. This will help with getting cleaner [diff outputs](https://ethereum.github.io/execution-specs/diffs/index.html).

When creating pull requests affecting multiple forks, we recommended submitting your PR in two steps:

1. Apply the changes on a single fork, open a _draft_ pull request, and get feedback; then
2. Apply the changes across the other forks, push them, and mark the pull request as ready for review.

This saves you having to apply code review feedback repeatedly for each fork.

### Development

Running the tests necessary to merge into the repository requires:

- [`uv`](https://docs.astral.sh/uv/) package manager,
- Python 3.11.x,
- [PyPy](https://www.pypy.org/) [7.3.19](https://downloads.python.org/pypy/) or later.
- `geth` installed and present in `$PATH`.

`execution-specs` depends on a submodule that contains common tests that are run across all clients, so we need to clone the repo with the --recursive flag. Example:

```bash
git clone --recursive https://github.com/ethereum/execution-specs.git
```

Or, if you've already cloned the repository, you can fetch the submodules with:

```bash
git submodule update --init --recursive
```

The tests can be run with:

```bash
tox
```

The development tools can also be run outside of `tox`, and can automatically reformat the code:

```bash
uv run ruff check        # Detects code issues and produces a report to STDOUT.
uv run ruff check --fix  # Fixes minor code issues (like unsorted imports).
uv run ruff format       # Formats code.
uv run mypy              # Verifies type annotations.
```

It is recommended to use a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) to keep your system Python installation clean.

A trace of the EVM execution for any test case can be obtained by providing the `--evm-trace` argument to pytest.
Note: Make sure to run the EVM trace on a small number of tests at a time. The log might otherwise get very big.
Below is an example.

```bash
uv run pytest \
    'tests/json_loader/test_state_tests.py::test_state_tests_frontier[stAttackTest - ContractCreationSpam - 0]' \
    --evm_trace
```

## CLI Utilities `ethereum_spec_tools`

The EELS repository has various CLI utilities that can help in the development process.

### New Fork Tool

This tool can be used to create the base code for a new fork by using the existing code from a given fork.

The command takes 4 arguments, 2 of which are optional

- from_fork: The fork name from which the code is to be duplicated. Eg. - "Tangerine Whistle"
- to_fork: The fork name of the new fork Eg - "Spurious Dragon"
- from_test (Optional): Name of the from fork within the test fixtures in case it is different from fork name. Eg. - "EIP150"
- to_test (Optional): Name of the to fork within the test fixtures in case it is different from fork name Eg - "EIP158"

As an example, if one wants to create baseline code for the `Spurious Dragon` fork from the `Tangerine Whistle` one

```bash
ethereum-spec-new-fork --from_fork="Tangerine Whistle" --to_fork="Spurious Dragon" --from_test=EIP150 --to_test=EIP158
```

The following will have to however, be updated manually

1. The fork number and `MAINNET_FORK_BLOCK` in `__init__.py`. If you are proposing a new EIP, please set `MAINNET_FORK_BLOCK` to `None`.
2. Any absolute package imports from other forks eg. in `trie.py`
3. Package names under `setup.cfg`
4. Add the new fork to the `monkey_patch()` function in `src/ethereum_optimized/__init__.py`
5. Adjust the underline in `fork/__init__.py`

### Sync Tool

The sync tool allows one to use an RPC provider to fetch and validate blocks against EELS.
The state can also be stored in a local DB after validation. Since syncing directly with the specs can be
very slow, one can also leverage the optimized module. This contains alternative implementations of routines
in EELS that have been optimized for speed rather than clarity/readability.

The tool can be called using the `ethereum-spec-sync` command which takes the following arguments

- rpc-url: Endpoint providing the Ethereum RPC API. Defaults to `http://localhost:8545/`
- unoptimized: Don't use the optimized state/ethash (this can be extremely slow)
- persist: Store the state in a db in this file
- geth: Use geth specific RPC endpoints while fetching blocks
- reset: Delete the db and start from scratch
- gas-per-commit: Commit to db each time this much gas is consumed. Defaults to 1_000_000_000
- initial-state: Start from the state in this db, rather than genesis
- stop-at: After syncing this block, exit successfully

- The following options are not supported WITH `--unoptimized` -> `--persist`, `--initial-state`, `--reset`
- The following options are not supported WITHOUT `--persist` -> `--initial_state`, `--reset`

### Patch Tool

This tool can be used to apply the unstaged changes in `SOURCE_FORK` to each of the `TARGET_FORKS`. If some
of the change didn't apply, '.rej' files listing the unapplied changes will be left in the `TARGET_FORK`.

The tool takes the following command line arguments

- The fork name where the changes have been made. Eg:- `frontier` (only a single fork name)
- The fork names where the changes have to be applied. Eg:- `homestead` (multiple values can be provided separated by space)
- optimized: Patch the optimized code instead
- tests: Patch the tests instead

As an example, if one wants to apply changes made in `Frontier` fork to `Homestead` and `Tangerine Whistle`

```bash
python src/ethereum_spec_tools/patch_tool.py frontier homestead tangerine_whistle
```

### Lint Tool

This tool checks for style and formatting issues specific to EELS and emits diagnostics
when issues are found

The tool currently performs the following checks

- The order of the identifiers between each hardfork is consistent.
- Import statements follow the relevant import rules in modules.

The command to run the tool is `ethereum-spec-lint`
