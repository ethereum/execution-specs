# Code Standards

This document outlines the coding standards and practices used in the @ethereum/execution-spec-tests repository.

## Code and CI Requirements

Code pushed to @ethereum/execution-spec-tests must fulfill the following checks in [CI](https://github.com/ethereum/execution-spec-tests/actions/workflows/tox_verify.yaml):

| Type                   | Tox Command                                     | Explanation                                                                                                 |
| ---------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Lint & code formatting | `uvx --with=tox-uv tox -e lint`                 | Python lint, format and module import check via `ruff`                                                      |
| Typecheck              | `uvx --with=tox-uv tox -e typecheck`            | Objects that provide typehints pass type-checking via `mypy`.                                               |
| Framework unit tests   | `uvx --with=tox-uv tox -e pytest`               | All framework unit tests must execute correctly.                                                            |
| EL Client test cases   | `uvx --with=tox-uv tox -e tests-deployed`       | All client test cases for deployed forks can be generated.                                                  |
| Benchmark EL Test cases    | `uvx --with=tox-uv tox -e tests-deployed-benchmark` | All client test cases specific to benchmarks for deployed forks can be generated.                               |
| HTML doc build         | `uvx --with=tox-uv tox -e mkdocs`               | Documentation generated without warnings.                                                                   |
| Spellcheck             | `uvx --with=tox-uv tox -e spellcheck`           | Code and documentation spell-check using codespell. |
| Markdown lint          | `uvx --with=tox-uv tox -e markdownlint`         | Markdown lint (requires [additional dependency](code_standards_details.md#additional-dependencies)).        |
| Changelog validation   | `uvx --with=tox-uv tox -e changelog`            | Validates changelog entries format and structure in `docs/CHANGELOG.md`.                                    |

!!! important "Avoid CI surprises - Use pre-commit hooks!"
    **We strongly encourage all contributors to install and use pre-commit hooks!** This will run fast checks (lint, typecheck, spellcheck) automatically before each commit, helping you catch issues early and avoid frustrating CI failures after pushing your changes.

    Install with one simple command:
    ```console
    uvx pre-commit install
    ```
    
    This saves you time by catching formatting issues, type errors, and spelling mistakes before they reach CI.

!!! tip "Running checks easily"

    Add an alias:

    ```console
    alias tox="uvx --with=tox-uv tox"
    ```

    Run all checks in parallel:

    ```console
    uvx --with=tox-uv tox run-parallel
    ```

    Run sequentially:

    ```console
    uvx --with=tox-uv tox
    ```

    Run specific, faster checks:

    ```console
    uvx --with=tox-uv tox -e lint,typecheck
    ```

!!! tip "Lint & code formatting: Using `ruff` and VS Code to help autoformat and fix module imports"

    On the command-line, solve fixable issues with:

    ```console
    uv run ruff check --fix
    ```

    Use VS Code, see [VS Code Setup](../getting_started/setup_vs_code.md), to autoformat code, automatically organize Python module imports and highlight typechecking and spelling issues.

!!! hint "Typechecking"

    Adding the correct typehints can sometimes be tricky and there are exceptions that require manually disabling typechecking on a per-line basis. Please reach out to the maintainers if you need help, either [directly](../getting_started/getting_help.md) or in a PR.

## Python Coding Preferences

- **Line Length**: 100 characters maximum.
- **Formatting**: Enforced by `ruff` (similar to `black`).
- **Documentation**: All public functions and classes should have docstrings
    - Docstrings should have a good one-line summary which uses the imperative ("Return" not "Returns").
    - Add a blank line after the summary for multi-line docstrings.
    - Single-line docstrings should have triple quotes on the same line.
- **Imports**: Use explicit imports (no `from module import *`).
- **Relative Imports**: Use relative imports within the same package
- **Error Handling**: Use explicit exception types and meaningful error messages.
- **Type Hints**: All functions should include type annotations.
- **Unused Function Arguments**: When  unavoidable, use `del`, e.g., `del unused_var`, at function start to avoid flagging linter errors.
- **Variable Naming**:
    - Use `snake_case` for variables, functions, and modules.
    - Use `PascalCase` for classes.
    - Use `UPPER_CASE` for constants.
- **File Paths**: Strongly prefer `pathlib` over `os.path` for file system operations.
- **Retry Logic**: Use [`tenacity`](https://github.com/jd/tenacity) library for handling flaky network connections and transient failures.

## Editor Setup

A correctly configured editor will automatically handle most formatting requirements. See [VS Code Setup](./setup_vs_code.md) for recommended settings.

## Detailed Information

See the [Detailed Code Standards](code_standards_details.md) page for more information on:

- [Running tox environments](code_standards_details.md#running-tox-environments).
    - Additional required [dependencies for markdownlint and spellchecking](code_standards_details.md#additional-dependencies).
- [Pre-commit hooks setup](code_standards_details.md#pre-commit-hooks).
- [Verifying test fixture changes](code_standards_details.md#verifying-fixture-changes).
- [Ignoring bulk change commits](code_standards_details.md#ignoring-bulk-change-commits) in `git blame`.
