# Useful Pytest Options

The EEST commands to run tests are customizations to the pytest framework, which provides many helpful options for test selection, parallel execution, report output and debugging. This section provides the most relevant options, a full overview is available in the [pytest docs](https://docs.pytest.org/en/8.3.x/).

## Fixture Inputs (Consume Commands)

See [Consume Cache and Fixture Inputs](./consume/cache.md).

## Dry-Run

List collected tests, `-q` restricts output to [test IDs](../filling_tests/test_ids.md) only:

```bash
uv run consume engine --input=<fixture_input> --collect-only -q
```

In `./hive` [standalone mode](./hive/index.md), this can be achieved via EEST's [`--sim.limit` "collectonly" prefix](./hive/common_options.md#collect-onlydry-run).

## Output Control

- `-v` - verbose output.
- `-vv` - more verbose output.
- `-s` - print stdout to the terminal during execution (don't capture it).
- `--eest-log-level=<LOG_LEVEL>` - write logs during test (helpful in combination with `-s`).

## Report Generation

JSON, HTML and XML reports can be generated with:

```bash
    --json-report \
    --json-report-file=report.json \
    --html=report.html \
    --junitxml=report.xml
```

## Test Case Selection Using Test IDs

In addition to Hive's regex-based `--sim.limit` option, running in dev mode supports pytest's `-k` syntax:

```bash
uv run consume rlp -k "test_chainid and fork_London"
uv run consume engine -k "eip1559 or eip4844" -m cancun
```

Use `--collect-only -q` to see which tests would run without executing them:

```bash
uv run consume engine --collect-only -q -k "fork_Prague"
```

## Test Case Selection using Marks

Select tests based on pytest [marks](../writing_tests/test_markers.md).

Run only state tests:

```bash
uv run consume direct --input=<fixture_input> -m state_test
```

Run blockchain tests for specific fork:

```bash
uv run consume engine --input=<fixture_input> -m "blockchain_test and cancun"
```

Combine marks with keyword filtering:

```bash
uv run consume engine --input=<fixture_input> -m "blockchain_test" -k "eip4844 or blob"
```

!!! note "Mark Availability"
    Not all test marks are available with consume commands. Fork and test type marks work reliably.

## Parallel Execution

Speed up test execution by running tests in parallel using pytest-xdist.

Auto-detect CPU count:

```bash
uv run consume engine --input=<fixture_input> -n auto
```

Specify worker count:

```bash
uv run consume direct --input=<fixture_input> -n 4
```

## Dropping in the Python Debugger

Dropping into the Python debugger can be helpful to inspect EEST simulator state or ssh to a client container. Adding the `--pdb` option will drop into Python debugger upon test failure, `-x` tells pytest to exit after the first fail:

```bash
uv run consume engine --pdb -x ...
```

### PDB Cheatsheet

- u  →  up the stack
- d → down the stack
- l  → list lines around current position
- ll → list entire function body
- p  → print expression
- pp → pretty-print expression

Sometimes `pp` is not enough and it's worth importing rich (`import rich`) in pdb and doing a `rich.print(obj)`.

## Early Exit Options

Stop after first failure:

```bash
uv run consume engine --input=<fixture_input> -x
```

Stop after N failures:

```bash
uv run consume rlp --input=<fixture_input> --maxfail=3
```

## Performance and Timing

Show slowest tests:

```bash
uv run consume engine --input=<fixture_input> --durations=10
```

Show all test durations:

```bash
uv run consume rlp --input=<fixture_input> --durations=0
```

Timeout control (per test):

```bash
uv run consume direct --input=<fixture_input> --timeout=30
```

Print relevant test stage timings such as client start-up, payload response time (`consume` only):

```bash
uv run consume engine --input=<fixture_input> --timing-data
```
