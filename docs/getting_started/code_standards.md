# Code Standards

This page outlines the code standards used in @ethereum/execution-specs. Many of the following preferences are enforced in CI via static code checks which can be ran locally via:

```console
just static
```

See [Verifying Changes](verifying_changes.md) for more details on running checks locally and ensuring that your code passes CI checks.

## Python Coding Preferences

- **Line Length**: 79 characters maximum.
- **Formatting**: Enforced by `ruff` (similar to `black`). Run `just fix` to format code via `ruff`.
- **Documentation**: All public functions and classes should have docstrings:
    - Docstrings should have a good one-line summary which uses the imperative ("Return" not "Returns").
    - Add a blank line after the summary for multi-line docstrings.
    - Single-line docstrings should have triple quotes on the same line.
- **Imports**: Use explicit imports (no `from module import *`).
- **Relative Imports**: Use relative imports within the same package.
- **Error Handling**: Use explicit exception types and meaningful error messages.
- **Type Hints**: All functions should include type annotations.
- **Unused Function Arguments**: When  unavoidable, use `del`, e.g., `del unused_var`, at function start to avoid flagging linter errors.
- **Variable Naming**:
    - Use `snake_case` for variables, functions, and modules.
    - Use `PascalCase` for classes.
    - Use `UPPER_CASE` for constants.
- **File Paths**: Strongly prefer `pathlib` over `os.path` for file system operations.
- **Retry Logic**: Use [`tenacity`](https://github.com/jd/tenacity) library for handling flaky network connections and transient failures.

## Testing Framework Plugins with Pytester

Use pytest's `pytester` fixture when writing tests for our pytest plugins and CLI commands.

`runpytest()` is the default. It runs the inner session in-process, is fast, and gives access to helpers like `assert_outcomes()` and `fnmatch_lines()`.

`runpytest_subprocess()` runs the inner session in a separate process. Use it only when in-process mode causes state leakage (e.g., Pydantic `ModelMetaclass` cache pollution or global mutation in `pytest_configure`). Subprocess isolation masks these bugs rather than fixing them, so prefer fixing the root cause and use subprocess mode as defense-in-depth.

Don't use raw `subprocess.run()` in pytester-based tests. If you need process isolation, use `runpytest_subprocess()`.

Both methods return a `RunResult` with `.ret`, `.outlines`, `.errlines`, `assert_outcomes()`, and `fnmatch_lines()`. When the inner test is expected to fail, use `capsys.readouterr()` after `runpytest_subprocess()` to suppress the inner failure output that pytester replays to stdout.
