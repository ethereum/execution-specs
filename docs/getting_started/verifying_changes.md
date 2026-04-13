# Verifying Changes

This page covers how to verify your changes before submitting a PR.

## Additional Dependencies for `markdownlint`

We use `markdownlint-cli2` to lint documentation markdown files, this is an external (non-Python) packages, that must be installed separately.

```console
sudo apt install nodejs
sudo npm install -g markdownlint-cli2@0.17.2  # the version used in ci
```

Or use a specific node version using `nvm`.

## Code and CI Requirements

Code pushed to @ethereum/execution-specs must pass the CI checks. Run `just` to see all available recipes, grouped by category. The most common checks:

```console
just fix      # Auto-fix formatting and lint issues
just static   # Run all static checks (lint, format, mypy, spellcheck, ...)
```

!!! tip "Lint & code formatting: Using `ruff` to help autoformat and fix module imports"

    On the command-line, solve fixable issues with:

    ```console
    just fix
    ```

!!! hint "Typechecking"

    Adding the correct typehints can sometimes be tricky and there are exceptions that require manually disabling typechecking on a per-line basis. Please reach out to the maintainers if you need help, either [directly](../getting_started/getting_help.md) or in a PR.

## Building and Verifying Docs Locally

Build the full HTML documentation:

```console
just docs
```

For faster iteration use (skips the "Test Case Reference" section):

```console
just docs-fast
```

## Verifying Test Fixture Changes

When writing a PR that modifies either the framework or test cases, verify that changes don't cause issues with existing test cases.

All filled fixtures contain a `hash` field in the `_info` object, which is used to verify that the fixture hasn't changed.

### Using the Hasher Tool

The `hasher` command can be used to bulk-verify the hashes of fixtures in a directory.

| Flag             | Description                                                       |
| ---------------- | ----------------------------------------------------------------- |
| `--files` / `-f` | Prints a combined hash per JSON fixture file.                     |
| `--tests` / `-t` | Prints the hash of every test vector in JSON fixture files.       |
| `--root` / `-r`  | Prints a combined hash for all JSON fixture files in a directory. |

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
| `--ignore-missing`  | Hide entries that exist in only one directory.            |
