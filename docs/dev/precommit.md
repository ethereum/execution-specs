# Enabling Pre-Commit Checks

There's a [pre-commit](https://pre-commit.com/) config file available in the repository root (`.pre-commit-config.yaml`) that can be used to enable automatic checks upon commit - the commit will not go through if the checks don't pass.

To enable pre-commit, the following must be run once:

```console
uvx pre-commit install
```

## What Gets Checked

Pre-commit runs the following checks on staged files:

| Check | Description |
|-------|-------------|
| `trailing-whitespace` | Removes trailing whitespace. |
| `end-of-file-fixer` | Ensures files end with a newline. |
| `check-yaml` | Validates YAML syntax. |
| `check-toml` | Validates TOML syntax. |
| `check-added-large-files` | Prevents large files from being committed. |
| `ruff check` | Python linting with auto-fix. |
| `ruff format` | Python formatting. |
| `codespell` | Spelling check for code and docs. |
| `mypy` | Python type checking. |
| `ethereum-spec-lint` | Custom Ethereum spec lints. |
| `uv lock --check` | Ensures lock file is up to date. |
| `actionlint` | GitHub Actions workflow validation. |
| `changelog` | Changelog format validation. |

!!! tip "Running checks manually"
    To run all fast checks without committing:

    ```console
    uvx tox -e check
    ```

!!! note "Bypassing pre-commit checks"
    Enabling of pre-commit checks is not mandatory (it cannot be enforced) and even if it is enabled, it can always be bypassed with:

    ```console
    git commit --no-verify
    ```
