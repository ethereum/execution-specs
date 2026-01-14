# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Package Overview

The `execution_testing` package is a library and framework for generating test vectors (test fixtures) from the Ethereum execution spec. It provides CLI tools and pytest plugins for test generation, execution, and consumption.

This package is a UV workspace member of the root repository.

## Directory Structure

```
packages/testing/
├── src/execution_testing/
│   ├── cli/              # Command-line tools
│   ├── test_types/       # Test fixture type definitions
│   ├── forks/            # Fork metadata and transitions
│   ├── specs/            # Test spec helpers
│   ├── fixtures/         # Fixture generation
│   ├── vm/               # VM helpers for test generation
│   ├── base_types/       # Fundamental types (Address, Hash, etc.)
│   ├── exceptions/       # Exception definitions
│   ├── tools/            # Utility tools
│   └── ...
├── stubs/                # Type stubs for external packages
└── pyproject.toml
```

## CLI Commands

### Primary Commands

- `fill` - Generate test fixtures from Python tests
- `consume` - Run fixtures against clients via simulators
- `execute` - Execute tests directly against clients
- `gentest` - Generate test stubs from templates

### Utility Commands

- `evm_bytes` - Convert bytecode manipulation utilities
- `hasher` - Hash computation tool for diffing fixtures.
- `genindex` - Generate fixture index files (used by consume for test discovery)

## Running Package Tests

```bash
# Via tox
uvx tox -e tests_pytest_py3

# Or directly via pytest
cd packages/testing && uv run pytest src/ -v
```

## Test Generation Pattern

Tests are Python functions that use fixtures from this package:

```python
from execution_testing.specs import StateTestFiller

@pytest.mark.valid_from("Shanghai")
def test_example(state_test: StateTestFiller):
    pre = {...}  # Pre-state
    tx = {...}   # Transaction
    post = {...} # Expected post-state
    state_test(pre=pre, tx=tx, post=post)
```

The `fill` command executes these tests and generates JSON fixtures.

## Key Concept

One test function auto-generates multiple fixture formats (`StateFixture`, `BlockchainFixture`, `BlockchainEngineFixture`). The `fill` command handles this transformation automatically.
