# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Directory Overview

This directory contains the Ethereum Execution Layer Specification (EELS) - a Python implementation of Ethereum that prioritizes readability and simplicity over performance.

## Design Philosophy

EELS is a **specification**, not a production implementation. It uses the **WET principle** (Write Everything Twice) instead of DRY:

- Every fork is a complete copy-paste of its predecessor
- Readability is prioritized over reducing code duplication
- Abstractions are avoided to keep each fork self-contained and understandable

Do **not** create abstractions to share code between forks, even if it feels repetitive.

## Package Structure

### `ethereum/`

The core specification implementation:

- **`forks/`** - Per-fork implementations (`frontier` → `homestead` → ... → `osaka` → `BPO1` → `BPO2` → ... → `amsterdam`)
- **`crypto/`** - Cryptographic primitives (hashing, signatures, BLS)
- **`utils/`** - Shared utilities
- **`ethash.py`** - Ethash proof-of-work algorithm
- **`genesis.py`** - Genesis block handling
- **`fork_criteria.py`** - Fork activation logic

### `ethereum_spec_tools/`

Development and tooling utilities:

- **`evm_tools/`** - t8n (transition tool), b11r (block builder), statetest
- **`lint/`** - EELS-specific linting rules
- **`new_fork/`** - Fork scaffolding tool
- **`sync.py`** - Block validation against RPC providers
- **`docc.py`** - Documentation generation

### `ethereum_optimized/`

Performance-optimized alternatives for sync operations (not for specification clarity).

## Fork Implementation Pattern

Each fork directory (`ethereum/forks/<fork_name>/`) follows a consistent structure:

```
<fork_name>/
├── __init__.py      # Fork metadata, MAINNET_FORK_BLOCK
├── blocks.py        # Block structure and validation
├── fork.py          # State transition functions
├── state.py         # State trie operations
├── transactions.py  # Transaction types and processing
├── trie.py          # Merkle Patricia Trie
├── utils/           # Fork-specific utilities
└── vm/
    ├── __init__.py
    ├── gas.py
    ├── instructions/  # EVM opcode implementations
    ├── interpreter.py
    ├── memory.py
    ├── precompiled_contracts/
    └── stack.py
```

## Working with Forks

### Branch Naming Conventions

- `mainnet` - Stable specs for forks live on mainnet
- `forks/<fork_name>` - Fork development branches (e.g., `forks/amsterdam`)
- `eips/<fork_name>/eip-<number>` - EIP feature branches (e.g., `eips/amsterdam/eip-7702`)

The **default branch** is set to the most actively developed fork. Most PRs should target this branch.

### Implementing a New EIP

1. Create branch from default: `eips/<fork_name>/eip-<number>`
2. Implement in `src/ethereum/<fork_name>/`
3. Run `uvx tox -e static` for sanity checks
4. PR against the target fork's branch (`forks/<fork_name>`)

### Creating a New Fork

```bash
ethereum-spec-new-fork --from_fork="Osaka" --to_fork="Amsterdam"
```

Then manually update: fork number, `MAINNET_FORK_BLOCK`, imports, `setup.cfg` packages.

## Critical Rules

### Import Isolation

Each fork is self-contained. Import rules enforced by `ethereum-spec-lint`:

- **Within same fork**: Use relative imports (`from . import vm`)
- **Previous fork**: Absolute imports allowed (`from ethereum.cancun import ...`)
- **Shared modules**: Always OK (`ethereum.crypto`, `ethereum.utils`)
- **Future/ancient forks**: Never allowed

### Adding New Features

- **New opcode**: Define in `vm/instructions/__init__.py`, implement in module, register in `op_implementation`, add gas cost
- **New precompile**: Create file in `vm/precompiled_contracts/`, add address constant and gas cost
- **New tx type**: Add class to `transactions.py`, update `Transaction` union, add exception if needed
