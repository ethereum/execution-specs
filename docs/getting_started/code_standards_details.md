# Detailed Code Standards

This page provides in-depth information about the code standards and verification processes in @ethereum/execution-spec-tests.

## Running Checks

Run all static checks:

```console
just static
```

Run `just` to list all available recipes. Individual checks can be run directly, for example:

```console
just lint
just typecheck
just spellcheck
```

### Additional Dependencies

Some checks require external (non-Python) packages:

#### For `spellcheck`

The spellcheck environment uses **codespell**, which is automatically installed via Python dependencies and checks for common spelling mistakes in code and documentation.

To fix spelling errors found by codespell:

```console
uv run codespell --write-changes
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

Certain checks can be run automatically as git pre-commit hooks to ensure that your changes meet the project's standards before committing.

### Installation

```console
uvx pre-commit install
```

For more information, see [Pre-commit Hooks Documentation](../dev/precommit.md).

## Testing Framework Plugins with Pytester

Use pytest's `pytester` fixture when writing tests for our pytest plugins and CLI commands.

`runpytest()` is the default. It runs the inner session in-process, is fast, and gives access to helpers like `assert_outcomes()` and `fnmatch_lines()`.

`runpytest_subprocess()` runs the inner session in a separate process. Use it only when in-process mode causes state leakage (e.g., Pydantic `ModelMetaclass` cache pollution or global mutation in `pytest_configure`). Subprocess isolation masks these bugs rather than fixing them, so prefer fixing the root cause and use subprocess mode as defense-in-depth.

Don't use raw `subprocess.run()` in pytester-based tests. If you need process isolation, use `runpytest_subprocess()`.

Both methods return a `RunResult` with `.ret`, `.outlines`, `.errlines`, `assert_outcomes()`, and `fnmatch_lines()`. When the inner test is expected to fail, use `capsys.readouterr()` after `runpytest_subprocess()` to suppress the inner failure output that pytester replays to stdout.

## Building and Verifying Docs Locally

Build the full HTML documentation:

```console
just docs
```

For faster iteration (skips the "[Test Case Reference](https://eest.ethereum.org/main/tests/)" section):

```console
just docs-fast
```

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

#### The `compare` Subcommand

The `hasher compare` subcommand directly compares two fixture directories
and shows only the differences:

```console
uv run hasher compare fixtures/ fixtures_new/
```

| Flag                | Description                                               |
| ------------------- | --------------------------------------------------------- |
| `--depth N` / `-d`  | Limit to N levels (0=root, 1=folders, 2=files, 3=tests).  |
| `--files` / `-f`    | Show differences at file level.                           |
| `--tests` / `-t`    | Show differences at individual test level.                |
| `--root` / `-r`     | Show only the root-level hash difference.                 |
| `--ignore-missing`  | Hide entries that exist in only one directory.             |
