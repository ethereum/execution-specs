# Contribution Guidelines

Help is always welcome and there are plenty of options to contribute to the Ethereum Execution Layer Specifications (EELS).

In particular, we appreciate support in the following areas:

- Reporting issues
- Fixing and responding to [issues](https://github.com/ethereum/execution-specs/issues), especially those tagged as [E-easy](https://github.com/ethereum/execution-specs/labels/E-easy) which are meant as introductory issues for external contributors.
- Improving the documentation.


For details about EELS usage and building, please refer the [README](https://github.com/ethereum/execution-specs/blob/master/README.md#usage)


## Contribution Guidelines

This specification aims to be:

1. **Correct** - Describe the _intended_ behavior of the Ethereum blockchain, and any deviation from that is a bug.
2. **Complete** - Capture the entirety of _consensus critical_ parts of Ethereum.
3. **Accessible** - Prioritize readability, clarity, and plain language over performance and brevity.

### Spelling and Naming

- Attempt to use descriptive English words (or _very common_ abbreviations) in documentation and identifiers.
- Avoid using EIP numbers in identifiers.
- If necessary, there is a custom dictionary `whitelist.txt`. 

### Changes across various Forks

Many contributions require changes across multiple forks, organized under `src/ethereum/*`. When making such changes, please ensure that differences between the forks are minimal and consist only of necessary differences. This will help with getting cleaner [diff outputs](https://ethereum.github.io/execution-specs/diffs/index.html).

When creating pull requests affecting multiple forks, we recommended submitting your PR in two steps:

1. Apply the changes on a single fork, open a _draft_ pull request, and get feedback; then
2. Apply the changes across the other forks, push them, and mark the pull request as ready for review.

This saves you having to apply code review feedback repeatedly for each fork.
 
### Development

Running the tests necessary to merge into the repository requires:

 * Python 3.11.x,
 * [PyPy](https://www.pypy.org/) [7.3.19](https://downloads.python.org/pypy/) or later
 * [`uv`](https://docs.astral.sh/uv/) package manager
 * `geth` installed and present in `$PATH`


`uv` can be installed via curl (recommended; can self-update):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or pip (requires Python, can't self-update):

```bash
pip install uv
```

Clone the repository and set up your development environment:

```bash
git clone https://github.com/ethereum/execution-specs.git
cd execution-specs
uv python install 3.11
uv python pin 3.11
uv sync --all-extras
```

The tests can be run with:
```bash
uvx --with=tox-uv tox
```

The development tools can also be run directly with `uv`, which handles the virtual environment automatically:

```bash
uv run ruff check src --fix          # Check and fix linting issues, format code, organize imports
uv run ruff format src               # Format code (similar to black)
uv run codespell -I whitelist.txt src # Check spelling
uv run mypy src --namespace-packages # Verify type annotations
uv run pytest -n 4                  # Run tests in parallel
uv run pytest -m "not slow"         # Run tests which execute quickly
```


The repository includes several tox environments for different testing scenarios:

- `static` - Linting, type checking, spell checking, and documentation build.
- `json_infra` - Tests for the JSON infrastructure.
- `py3` - Run execution spec tests using CPython.
- `pypy3` - Run execution spec tests using PyPy.

You can run specific tox environments individually, e,g:

```bash
uvx --with=tox-uv tox -e static        # Run linting and type checking.
```

Or run all environments in parallel:

```bash
uvx --with=tox-uv tox run-parallel
```

The specification tests can also be ran directly:

```bash
uv run ethereum-spec-fill tests/eest --clean --until Osaka
```

A trace of the EVM execution for any test case can be obtained by providing the `--evm-trace` argument to pytest.
Note: Make sure to run the EVM trace on a small number of tests at a time. The log might otherwise get very big.
Below is an example.

```bash
uv run pytest tests/frontier/test_state_transition.py -k 'test_general_state_tests_new' --evm-trace
```

## Code Standards

The codebase follows specific formatting and linting standards enforced by `ruff`, which replaces `black`, `isort`, and `flake8`:

- **Line Length**: 79 characters maximum.
- **Formatting**: Enforced by `ruff format` (similar to `black`).
- **Import Sorting**: Handled by `ruff check` (similar to `isort`).
- **Linting**: Code quality checks via `ruff check`.
- **Type Checking**: Enforced by `mypy` for type annotations.
- **Spell Checking**: Documentation and comments checked by `codespell`

All these standards are automatically checked in CI via the `static` tox environment. You can run the checks locally:

```bash
uvx --with=tox-uv tox -e static
```

## CLI Utilities `ethereum_spec_tools`

The EELS repository has various CLI utilities that can help in the development process.

### New Fork Tool
-----------------
This tool can be used to create the base code for a new fork by using the existing code from a given fork.

The command takes 4 arguments, 2 of which are optional
 * from_fork: The fork name from which the code is to be duplicated. Eg. - "Tangerine Whistle"
 * to_fork: The fork name of the new fork Eg - "Spurious Dragon"
 * from_test (Optional): Name of the from fork within the test fixtures in case it is different from fork name. Eg. - "EIP150"
 * to_test (Optional): Name of the to fork within the test fixtures in case it is different from fork name Eg - "EIP158"

As an example, if one wants to create baseline code for the `Spurious Dragon` fork from the `Tangerine Whistle` one

```bash
uv run ethereum-spec-new-fork --from_fork="Tangerine Whistle" --to_fork="Spurious Dragon" --from_test=EIP150 --to_test=EIP158
```

The following will have to however, be updated manually
 1. The fork number and `MAINNET_FORK_BLOCK` in `__init__.py`. If you are proposing a new EIP, please set `MAINNET_FORK_BLOCK` to `None`.
 2. Any absolute package imports from other forks eg. in `trie.py`
 3. Package names under `setup.cfg`
 4. Add the new fork to the `monkey_patch()` function in `src/ethereum_optimized/__init__.py`
 5. Adjust the underline in `fork/__init__.py`


### Sync Tool
-------------
The sync tool allows one to use an RPC provider to fetch and validate blocks against EELS.
The state can also be stored in a local DB after validation. Since syncing directly with the specs can be
very slow, one can also leverage the optimized module. This contains alternative implementations of routines
in EELS that have been optimized for speed rather than clarity/readability.


The tool can be called using the `uv run ethereum-spec-sync` command which takes the following arguments
 * rpc-url: Endpoint providing the Ethereum RPC API. Defaults to `http://localhost:8545/`
 * unoptimized: Don't use the optimized state/ethash (this can be extremely slow)
 * persist: Store the state in a db in this file
 * geth: Use geth specific RPC endpoints while fetching blocks
 * reset: Delete the db and start from scratch
 * gas-per-commit: Commit to db each time this much gas is consumed. Defaults to 1_000_000_000
 * initial-state: Start from the state in this db, rather than genesis
 * stop-at: After syncing this block, exit successfully

- The following options are not supported WITH `--unoptimized` -> `--persist`, `--initial-state`, `--reset`
- The following options are not supported WITHOUT `--persist` -> `--initial_state`, `--reset`


### Patch Tool
--------------
This tool can be used to apply the unstaged changes in `SOURCE_FORK` to each of the `TARGET_FORKS`. If some
of the change didn't apply, '.rej' files listing the unapplied changes will be left in the `TARGET_FORK`.


The tool takes the following command line arguments
 * The fork name where the changes have been made. Eg:- `frontier` (only a single fork name)
 * The fork names where the changes have to be applied. Eg:- `homestead` (multiple values can be provided separated by space)
 * optimized: Patch the optimized code instead
 * tests: Patch the tests instead

As an example, if one wants to apply changes made in `Frontier` fork to `Homestead` and `Tangerine Whistle`

```bash
uv run ethereum-spec-patch frontier homestead tangerine_whistle
```

### Lint Tool
-------------
This tool checks for style and formatting issues specific to EELS and emits diagnostics
when issues are found

The tool currently performs the following checks
- The order of the identifiers between each hardfork is consistent.
- Import statements follow the relevant import rules in modules.

The command to run the tool is `uv run ethereum-spec-lint`
