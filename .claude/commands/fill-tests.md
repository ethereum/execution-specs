# Fill Tests

CLI reference for the `fill` command. Run this skill before filling test fixtures. The `fill` command is pytest-based — all standard pytest flags work.

## Basic Usage

```
uv run fill tests/                                    # Fill all tests
uv run fill tests/cancun/ --fork Cancun               # Specific fork
uv run fill tests/path/to/test.py -k "test_name"      # Specific test
uv run fill tests/osaka/ --until Osaka                 # Up to fork (inclusive)
uv run fill --collect-only tests/                      # Dry run: list tests without executing
```

## Key Flags

- `--fork FORK` / `--until FORK` — target specific fork or range
- `--output DIR` + `--clean` — output directory; `--clean` required when re-filling
- `-k "pattern"` — filter tests by name pattern
- `-m "marker"` — filter by pytest marker (e.g. `-m state_test`, `-m blockchain_test`)
- `-n auto --maxprocesses N` — parallel execution (use `--dist=loadgroup`)
- `--evm-bin PATH` — specify t8n tool (default: `ethereum-spec-evm-resolver`)
- `--verify-fixtures` — verify generated fixtures against geth blocktest
- `--generate-all-formats` — generate all fixture formats (2-phase)

## Debugging

- `--evm-dump-dir DIR` — dump t8n input/output for debugging
- `--traces` — collect execution traces
- `--pdb` — drop into debugger on failure
- `-vv` — verbose output; `-x` — stop on first failure; `-s` — print stdout

## Watch Mode

- `--watch` — re-run on file changes (clears screen between runs)
- `--watcherfall` — same but keeps output history

## Benchmark Tests

- Must use `-m benchmark` — benchmark tests are excluded by default
- Require evmone as backend: `--evm-bin=evmone-t8n`
- Default benchmark fork is Prague (set in `tests/benchmark/conftest.py`)
- Gas values mode: `--gas-benchmark-values 1,10,100` (values in millions of gas)
- Fixed opcode count mode: `--fixed-opcode-count 1,10,100` (values in thousands)
- These two modes are **mutually exclusive**
- Use `--generate-pre-alloc-groups` for stateful benchmarks

## Static Tests (Legacy)

- `uv run fill --fill-static-tests tests/static/` — fills YAML/JSON fillers from `ethereum/tests`
- Legacy only — do NOT add new static fillers. Use Python tests instead
- Useful to check if spec changes broke how legacy tests fill

## Fixture Formats

One test function auto-generates multiple formats: `StateFixture`, `BlockchainFixture`, `BlockchainEngineFixture`. Use `--generate-all-formats` for additional formats via 2-phase execution.

## References

See `docs/filling_tests/` for detailed documentation.
