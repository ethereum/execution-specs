# Implement EIP

Patterns for implementing spec changes in `src/ethereum/forks/`. Run this skill before implementing an EIP or modifying fork code.

## Fork Directory Layout

Each fork lives at `src/ethereum/forks/<fork_name>/`. Explore the latest fork directory for current structure. Key files:

- `__init__.py` — FORK_CRITERIA, fork metadata
- `fork.py` — state transition functions
- `blocks.py` — block structure and validation
- `transactions.py` — transaction types and processing
- `state.py` — state trie operations
- `vm/instructions/__init__.py` — Ops enum + `op_implementation` dict
- `vm/gas.py` — gas constants and calculations
- `vm/precompiled_contracts/__init__.py` — precompile address constants
- `vm/precompiled_contracts/mapping.py` — `PRE_COMPILED_CONTRACTS` registry

## Import Isolation (enforced by `ethereum-spec-lint`)

- **Within same fork**: relative imports (`from . import vm`, `from .state import ...`)
- **Previous fork only**: absolute imports (`from ethereum.cancun import ...`)
- **Shared modules**: always OK (`ethereum.crypto`, `ethereum.utils`, `ethereum.exceptions`)
- **Future forks**: NEVER allowed
- **Ancient forks (2+ back)**: NEVER allowed
- Run `ethereum-spec-lint` to verify before committing

## Adding a New Opcode

1. Add to `Ops` enum in `vm/instructions/__init__.py` with hex value
2. Implement function in appropriate `vm/instructions/<category>.py` — follows pattern: STACK → GAS (`charge_gas`) → OPERATION → PROGRAM COUNTER
3. Register in `op_implementation` dict in `vm/instructions/__init__.py`
4. Add gas constant in `vm/gas.py` if needed

## Adding a New Precompile

1. Define address constant in `vm/precompiled_contracts/__init__.py` using `hex_to_address("0x...")`
2. Create implementation file `vm/precompiled_contracts/<name>.py`
3. Register in `PRE_COMPILED_CONTRACTS` dict in `vm/precompiled_contracts/mapping.py`
4. Add gas constant in `vm/gas.py`

## Adding a New Transaction Type

1. Define `@slotted_freezable @dataclass` class in `transactions.py`
2. Add to `Transaction` union type at bottom of file
3. Handle in `fork.py` validation/processing logic
4. Add exception type in `exceptions.py` if needed

## Creating a New Fork

```bash
uv run ethereum-spec-new-fork --new-fork=<name> --template-fork=<template>
```

- Copies all files from template fork and applies codemods (renames, constant updates)
- After running: update `__init__.py` docstring, fork-specific constants, run `uv run ruff format`
- Fork criteria types: `ByBlockNumber(N)` (pre-merge), `ByTimestamp(T)` (post-merge), `Unscheduled(order_index=N)` (in development)

## Branch Naming

- Feature branches: `eips/<fork_name>/eip-<number>`
- PR targets: `forks/<fork_name>`
