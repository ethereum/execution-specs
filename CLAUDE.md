# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **Ethereum Execution Layer Specification** written in Python. It serves as the reference implementation in order to generate tests for Ethereum execution clients.

### Key Components

- **`./src/`** - The executable specification for the Ethereum execution layer.
- **`./tests/`** - Consensus tests and benchmarking tests for Ethereum execution layer clients (expressed as pytest tests).
- **`./packages/testing/`** - The `execution_testing` package: a library and framework for generating test vectors (test fixtures) from the spec and consensus tests.

### Branch Structure

- **Default branch** is the most actively developed fork (currently `forks/amsterdam`).
- `mainnet` branch contains stable specs for forks live on mainnet.
- Most PRs should target the default branch.

## Tooling

- **uv** is the package manager for all tooling.
- **tox** orchestrates test environments (`uvx tox -al`).
- The `execution_testing` package under `packages/testing/` is a UV workspace member.

## Common Commands

### Linting and Static Analysis

Run all static code checks before committing:

```bash
uvx tox -e static
```

```bash
uv run ruff format                     # Format code
uv run ruff check --output-format=json # Check for issues
uv run ruff check --fix                # Auto-fix issues
uv run mypy                            # Type checking
uv run codespell                       # Spell checking
ethereum-spec-lint                     # Import hygiene across forks
```

### Running Tests

```bash
# Run all tox environments (slow!)
uvx tox

# Run specific tox environments
uvx tox -e static              # Linting, typing, spell check
uvx tox -e json_infra          # Run spec against released test fixtures
uvx tox -e py3                 # Fill consensus tests using EELS (Python)
```

### Generating Test Fixtures (fill command)

Test vectors are also called "test fixtures":

```bash
uv run fill tests/                           # Fill all tests
uv run fill tests/cancun/ --fork Cancun      # Fill specific fork tests
uv run fill tests/path/to/test.py -k "test_name"  # Fill specific test
```

### Documentation

The repository has two orthogonal documentation systems:

1. `docc` is dedicated tool used to generate documentation from the spec Python source code.

    ```bash
    uvx tox -e spec-docs    # Generate spec docs with docc - slow!
    ```

2. `mkdocs` is used to generate HTML documentation from the markdown in `./docs/`.

    ```bash
    uv run mkdocs serve     # Live preview docs at localhost:8000
    ```

## Architecture

### Fork Structure

Each Ethereum hard fork has its own implementation under `src/ethereum/forks/`:

- Fork order: `frontier` → `homestead` → ... → `osaka` → `BPO1` → `BPO2` → ... → `amsterdam`.
- Each fork is a complete copy of its predecessor (WET principle—readability over DRY).
- Each fork contains: `__init__.py`, `vm/`, `utils/`, and fork-specific modules.

### Test Organization

Tests in `./tests/` are organized by the fork in which the tested functionality was introduced in:

- `tests/<fork>/eip<number>/` - Tests for specific EIPs
- `tests/benchmark/` - Gas benchmarking tests
- `tests/json_infra/` - Infrastructure for running JSON test fixtures

### Key CLI Tools

- `ethereum-spec-lint` - Import hygiene across forks
- `ethereum-spec-new-fork` - Create baseline code for new forks
- `fill` - Generate test fixtures from spec

## Code Style

- Line length: 79 characters
- Type annotations required (strict mypy)
- Naming: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- Use descriptive English words, avoid EIP numbers in identifiers
- Docstrings: imperative mood ("Return" not "Returns"), blank line after summary for multi-line
- Prefer `pathlib` over `os.path` for file paths
- Custom dictionary for spell checking: `whitelist.txt`
