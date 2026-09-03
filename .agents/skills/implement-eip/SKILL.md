---
name: implement-eip
description: Implement EIP specification changes using repository conventions.
---

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
2. Implement function in appropriate `vm/instructions/<category>.py` — follows pattern: STACK → GAS (`charge_gas`) → OPERATION → PROGRAM COUNTER. Opcodes that touch state use the staged gas labels — see "Gas Handling" below.
3. Register in `op_implementation` dict in `vm/instructions/__init__.py`
4. Add gas constant in `vm/gas.py` if needed

## Gas Handling

Recent forks meter two gas dimensions: execution gas and state gas (for durable state growth). Key rules:

1. Gas constants and calculations go in `vm/gas.py`; a frame's mutable gas state lives on `Evm.gas_meter`.
2. Extend the named helper vocabulary (`charge_*`, `credit_*`, `restore_*`, `withhold_*`, ...) instead of doing gas arithmetic by hand at call sites; encode each helper's invariant as an assert.
3. State gas is charged by the frame whose opcode causes the creation, before the child's execution-gas share is withheld; the whole reservoir passes to the child.
4. A failing frame settles its own meter before returning, so parents incorporate children unconditionally.
5. Opcodes that touch state use labeled stages, with all charging before the operation: `GAS (STATE-INDEPENDENT)` → `STATE ACCESS (STATE-DEPENDENT GAS)` → `STATE GAS` → `CHILD GRANT` → `OPERATION`. Simple opcodes keep the bare `GAS` marker. `generic_call`/`generic_create` contain no pricing; they run the child lifecycle: `PREFLIGHT` → `DESTINATION ACCESS` → `CHILD GRANT` → `DISPATCH` → `OUTCOME`.
6. Avoid "frame" in gas identifiers (a future EIP claims the term); when a name diverges from the spec's variable name, cross-reference the spec name in the docstring.
7. A gas change is behavior-preserving only if the relative order of every charge, check, and trace event is unchanged; verify with the gas-related fill tests under `tests/<fork>/`.

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
