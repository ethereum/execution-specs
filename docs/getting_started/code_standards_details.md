# Detailed Code Standards

This page provides in-depth information about the code standards and verification processes in @ethereum/execution-spec-tests.

## Running Tox Environments

### Execution Options

Run all `tox` environments in parallel:

```console
uvx --with=tox-uv tox run-parallel
```

Run environments sequentially with verbose output:

```console
uvx --with=tox-uv tox -v
```

List all available environments:

```console
uvx --with=tox-uv tox -av
```

### Specific Environment Commands

Run specific environments using the `-e` flag:

```console
uvx --with=tox-uv tox -e lint,typecheck,spellcheck
```

#### For Test Case Changes (`./tests/`)

```console
uvx --with=tox-uv tox -e lint,typecheck,spellcheck,tests-deployed
```

#### For Framework and Library Changes (`./src/`)

```console
uvx --with=tox-uv tox -e lint,typecheck,spellcheck,pytest
```

#### For Documentation Changes (`./docs/`)

```console
uvx --with=tox-uv tox -e spellcheck,markdownlint,mkdocs,changelog
```

!!! note "Tox Virtual Environment"
Checks performed by `tox` are sandboxed in their own virtual environments (created automatically in the `.tox/` subdirectory). These can be used to debug errors encountered during `tox` execution.

### Additional Dependencies

Some checks require external (non-Python) packages:

#### For `spellcheck`

The spellcheck environment uses **codespell**, which is automatically installed via Python dependencies and checks for common spelling mistakes in code and documentation.

To fix spelling errors found by codespell:

```console
uv run codespell *.md *.ini .github/ src/ tests/ docs/ --write-changes
```

!!! note "VS Code Integration"
    The `whitelist.txt` file is still maintained for the VS Code cSpell extension, which provides real-time spell checking in the editor.

#### For `markdownlint`

```console
sudo apt install nodejs
sudo npm install -g markdownlint-cli2@0.17.2  # the version used in ci
```

Or use a specific node version using `nvm`.

## Pre-commit Hooks

Certain `tox` environments can be run automatically as git pre-commit hooks to ensure that your changes meet the project's standards before committing.

### Installation

```console
uvx pre-commit install
```

For more information, see [Pre-commit Hooks Documentation](../dev/precommit.md).

## Formatting and Line Length

The Python code in @ethereum/execution-spec-tests is formatted with `ruff` with a line length of 100 characters.

### Ignoring Bulk Change Commits

The maximum line length was changed from 80 to 100 in Q2 2023. To ignore this bulk change commit in git blame output, use the `.git-blame-ignore-revs` file:

```console
git blame --ignore-revs-file .git-blame-ignore-revs docs/gen_test_case_reference.py
```

To use the revs file persistently with `git blame`:

```console
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

## Building and Verifying Docs Locally

To quickly build and browse the HTML documentation locally run:

=== "bash"

    ```console
    export FAST_DOCS=True
    uv run mkdocs serve
    ```

=== "fish"

    ```console
    set -x FAST_DOCS True
    uv run mkdocs serve
    ```

Setting `FAST_DOCS` to `False` additionally builds the "[Test Case Reference](https://eest.ethereum.org/main/tests/)" Section.

## Verifying Fixture Changes

When writing a PR that modifies either the framework or test cases, verify that changes don't cause issues with existing test cases.

All filled fixtures contain a `hash` field in the `_info` object, which is used to verify that the fixture hasn't changed.

### Using the Hasher Tool

The `hasher` command can be used to bulk-verify the hashes of fixtures in a directory.

| Flag             | Description                                                       |
| ---------------- | ----------------------------------------------------------------- |
| `--files` / `-f` | Prints a combined hash per JSON fixture file.                     |
| `--tests` / `-t` | Prints the hash of every test vector in JSON fixture files.       |
| `--root` / `-r`  | Prints a combined hash for all JSON fixture files in a directory. |

For a quick comparison between two fixture directories:

```console
hasher --root fixtures/
hasher --root fixtures_new/
```

To identify which files are different:

```console
diff <(hasher --files fixtures/) <(hasher --files fixtures_new/)
```

For a granular comparison:

```console
diff <(hasher --tests fixtures/) <(hasher --tests fixtures_new/)
```
