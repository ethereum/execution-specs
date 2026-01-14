# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Directory Overview

This directory contains consensus tests and benchmarking tests for Ethereum execution layer clients. Tests are written in Python and generate JSON test fixtures that can be consumed by any Ethereum client.

## Directory Structure

### Fork-Based Test Organization

Tests are organized by the fork they target:

- `tests/frontier/`, `tests/homestead/`, ... `tests/osaka/`
- Within each fork: `tests/<fork>/eip<number>/` for EIP-specific tests
- `tests/unscheduled/` - Tests for EIPs not yet scheduled for a fork

### Special Directories

- **`benchmark/`** - Gas benchmarking tests (stateful, fuzzy-compute)
- **`json_infra/`** - Infrastructure for running JSON test fixtures against the spec
- **`evm_tools/`** - Tests for the EVM tooling (t8n, b11r)
- **`common/`** - Shared test utilities
- **`static/`** - Legacy tests from ethereum/tests in JSON/YAML format (use `uv run fill --fill-static-tests`)
- **`fixtures/`** - Test fixture data

## Running Tests

### Fill Tests (Generate Fixtures)

The `fill` command is pytest-based, it has access to all pytest's regular flags.

```bash
uv run fill tests/                                  # All tests
uv run fill tests/cancun/ --fork Cancun             # Specific fork
uv run fill tests/cancun/eip4844_blobs/ -k "test_blob"  # Pattern match
uv run fill tests/osaka/ --until Osaka              # Up to specific fork
uv run fill tests/ --output=fixtures --clean        # Overwrite existing fixtures directory
```

Use `--clean` to overwrite existing fixture directories (required for re-filling).

## Writing Tests

Tests use the `execution_testing` framework from `packages/testing/`. Key patterns:

### Test Formats

- Prefer `state_test` for single transactions (simpler, avoids block-building false positives)
- `fill` auto-generates a `blockchain_test` for every `state_test`
- Use `blockchain_test` only when testing multi-block scenarios

### Basic State Test

```python
@pytest.mark.valid_from("Cancun")
def test_example(state_test: StateTestFiller):
    # Setup pre-state, transaction, expected post-state
    state_test(...)
```

### Markers

- `@pytest.mark.valid_from("Fork")` - Test applies from this fork onward
- `@pytest.mark.slow` - Marks slow tests (excluded by default)
- `@pytest.mark.benchmark` - Gas benchmarking tests

## Quick Reference

### Setup Helpers

```python
sender = pre.fund_eoa()                    # Create funded EOA
addr = pre.deploy_contract(code=Op.STOP)   # Deploy contract

# Anti-pattern: Do NOT manipulate pre dict directly
# pre[addr] = Account(balance=10**18)      # Wrong!
```

### Required Markers

Always mark fork validity:

```python
@pytest.mark.valid_from("Cancun")
def test_example(state_test: StateTestFiller):
    ...
```

### Exception Tests

```python
state_test(..., block_exception=TransactionException.INTRINSIC_GAS_TOO_LOW)
```
