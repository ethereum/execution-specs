# Code Standards

This document outlines the coding standards and practices used in the @ethereum/execution-specs repository.

## Code and CI Requirements

Code pushed to @ethereum/execution-specs must fulfill the following checks in [CI](https://github.com/ethereum/execution-specs/actions/workflows/check.yaml):

| Type                   | Command                                         | Explanation                                                                                                 |
| ---------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **All static checks**  | `just check` / `make check` / `uvx tox -e check`| Run all static checks (lint, format, typecheck, spellcheck, etc.) in sequence.                              |
| Lint                   | `uvx tox -e lint`                 | Python lint check via `ruff`.                                                                               |
| Format                 | `uvx tox -e format`               | Python code formatting check via `ruff`.                                                                    |
| Typecheck              | `uvx tox -e typecheck`            | Objects that provide typehints pass type-checking via `mypy`.                                               |
| Framework unit tests   | `uvx tox -e tests_pytest_py3`     | All framework unit tests must execute correctly.                                                            |
| Fill tests             | `uvx tox -e py3`                  | All test cases for deployed forks can be generated.                                                         |
| Benchmark tests        | `uvx tox -e benchmark-gas-values` | Benchmark test cases can be generated.                                                                      |
| HTML doc build         | `uvx tox -e mkdocs`               | Documentation generated without warnings.                                                                   |
| Spellcheck             | `uvx tox -e spellcheck`           | Code and documentation spell-check using codespell.                                                         |
| Markdown lint          | `uvx tox -e markdownlint`         | Markdown lint (requires [additional dependency](code_standards_details.md#additional-dependencies)).        |
| Changelog validation   | `uvx tox -e changelog`            | Validates changelog entries format and structure in `docs/CHANGELOG.md`.                                    |

!!! important "Avoid CI surprises - Use pre-commit hooks!"
    **We strongly encourage all contributors to install and use pre-commit hooks!** This will run fast checks (lint, typecheck, spellcheck) automatically before each commit, helping you catch issues early and avoid frustrating CI failures after pushing your changes.

    Install with one simple command:
    ```console
    uvx pre-commit install
    ```

    This saves you time by catching formatting issues, type errors, and spelling mistakes before they reach CI.

!!! tip "Running checks easily"

    Run all static checks (recommended before pushing):

    ```console
    just check      # or: make check, uvx tox -e check
    ```

    Auto-fix lint and format issues:

    ```console
    just fix        # or: make fix
    ```

    Run specific checks:

    ```console
    just lint       # or: uvx tox -e lint
    just typecheck  # or: uvx tox -e typecheck
    ```

    See [Build Tools](../dev/build_tools.md) for all available commands.

!!! info "Fix hints on failure"

    When a check fails, you'll see a **fix hint** with instructions on how to resolve the issue:

    ```
    ============================================================
    Python lint check (via ruff) failed:
    ============================================================
    Try:
        uv run ruff check --fix .

    Verify:
    uv run ruff check
    ============================================================
    ```

    In GitHub Actions, these hints also appear in the job summary for easy access.

!!! tip "Lint & code formatting: Using `ruff` and VS Code to help autoformat and fix module imports"

    On the command-line, solve fixable issues with:

    ```console
    just fix        # or: make fix
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
