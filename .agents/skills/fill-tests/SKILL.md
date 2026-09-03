---
name: fill-tests
description: Fill test fixtures with the repository fill command.
---

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
- `--evm-bin PATH` — t8n tool; defaults to the in-repo EELS Python spec (`src/ethereum/`)
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

- Excluded from a broad `tests/` run: include them by targeting a `tests/benchmark/...` path, or add `--include-benchmark` when also collecting `tests/`.
- Pick a mode (mutually exclusive): `--gas-benchmark-values 1,10,100` (millions of gas) or `--fixed-opcode-count 1,10,100` (thousands). These parametrize the tests, e.g. `...[fork_Prague-blockchain_test-benchmark-gas-value_1M]`.
- Backend is optional: omitting `--evm-bin` runs the slow in-repo EELS Python spec; `--evm-bin=evmone` or `--evm-bin=evm` (geth, used by `just bench-gas`) are faster.

## Fixture Formats

One test function auto-generates multiple formats: `StateFixture`, `BlockchainFixture`, `BlockchainEngineFixture`. Use `--generate-all-formats` for additional formats via 2-phase execution.

## References

See `docs/filling_tests/` for detailed documentation.
