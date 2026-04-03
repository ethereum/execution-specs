# Pytester

Guide for pytester-based plugin/CLI tests. Run before writing or modifying these tests.

## Which execution mode to use

- **`runpytest()`** — default. In-process, fast, full `RunResult` API (`assert_outcomes()`, `fnmatch_lines()`).
- **`runpytest_subprocess()`** — use only when in-process causes state leakage (Pydantic cache pollution, global mutation in `pytest_configure`). Same `RunResult` API.
- **Raw `subprocess.run()`** — never use alongside pytester. Use `runpytest_subprocess()` instead.

Subprocess isolation masks bugs rather than fixing them. Prefer fixing the root cause and use subprocess as defense-in-depth.

## Expected inner failures

`runpytest_subprocess()` replays inner output to outer stdout (by design). Suppress with `capsys.readouterr()`:

```python
def test_expected_failure(pytester: Any, capsys: Any, pytestconfig: Any) -> None:
    result = pytester.runpytest_subprocess(...)
    capsys.readouterr()  # suppress inner failure bleed
    assert result.ret != 0
    output = "\n".join(result.outlines + result.errlines)
    # conditional print for -s debugging
    if pytestconfig.getoption("capture") == "no":
        with capsys.disabled():
            print(output)
```

## RunResult API

Prefer `assert_outcomes()` and `fnmatch_lines()` over manual `any(... in line ...)` — better failure messages.

- `result.ret` — exit code
- `result.outlines` / `result.errlines` — line lists
- `result.assert_outcomes(passed=N, failed=N)`
- `result.stdout.fnmatch_lines(["*pattern*"])`
