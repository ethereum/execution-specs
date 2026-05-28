# GasCosts Reference

This page lists the `GasCosts` fields and the opcodes they affect. Use this as
a reference when creating or editing a `gas_repricing.json` config file to help
you know which field to override.

For an up-to-date, fork-specific mapping, run:

```bash
uv run gas-map --fork <ForkName>
```

## Base Operation Costs

| GasCosts Field | Typical Value | Affected Opcodes |
|---|---|---|
| `VERY_LOW` | 3 | ADD, SUB, CALLDATALOAD, LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, XOR, NOT, BYTE, SHL, SHR, SAR, SIGNEXTEND, PUSH1-PUSH32, DUP1-DUP16, SWAP1-SWAP16, MLOAD, MSTORE, MSTORE8 |
| `LOW` | 5 | MUL, DIV, SDIV, MOD, SMOD, CLZ |
| `MID` | 8 | ADDMOD, MULMOD, JUMP |
| `HIGH` | 10 | JUMPI |
| `BASE` | 2 | ADDRESS, ORIGIN, CALLER, CALLVALUE, CALLDATASIZE, CODESIZE, GASPRICE, COINBASE, TIMESTAMP, NUMBER, PREVRANDAO, GASLIMIT, POP, PC, MSIZE, GAS, RETURNDATASIZE, CHAINID, SELFBALANCE, BASEFEE, BLOBBASEFEE |
| `OPCODE_JUMPDEST` | 1 | JUMPDEST |
| `OPCODE_BLOCKHASH` | 20 | BLOCKHASH |

## Storage Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `WARM_SLOAD` | 100 | SLOAD when slot is warm |
| `COLD_STORAGE_ACCESS` | 2100 | SLOAD when slot is cold |
| `STORAGE_SET` | 20000 | SSTORE: setting a slot from zero to non-zero |
| `STORAGE_RESET` | 2900 | SSTORE: updating an existing non-zero slot or resetting to original value |
| `COLD_STORAGE_WRITE` | 5000 | SSTORE write involving a cold storage slot |

## Account Access Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `WARM_ACCESS` | 100 | BALANCE, EXTCODESIZE, etc. when warm |
| `COLD_ACCOUNT_ACCESS` | 2600 | BALANCE, EXTCODESIZE, etc. when cold |
| `TX_ACCESS_LIST_ADDRESS` | 2400 | Per address in access list |
| `TX_ACCESS_LIST_STORAGE_KEY` | 1900 | Per storage key in access list |

## Exponentiation

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `OPCODE_EXP_BASE` | 10 | EXP base cost |
| `OPCODE_EXP_PER_BYTE` | 50 | EXP per byte of exponent |

## Memory and Copy

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `MEMORY_PER_WORD` | 3 | Memory expansion cost coefficient |
| `OPCODE_COPY_PER_WORD` | 3 | Per-word copy cost (CALLDATACOPY, CODECOPY, etc.) |
| `OPCODE_KECCAK256_BASE` | 30 | SHA3 base cost |
| `OPCODE_KECCACK256_PER_WORD` | 6 | SHA3 per 32-byte word |

## Logging

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `OPCODE_LOG_BASE` | 375 | LOG base cost |
| `OPCODE_LOG_DATA_PER_BYTE` | 8 | LOG per byte of data |
| `OPCODE_LOG_TOPIC` | 375 | LOG per topic |

## Transaction Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `TX_BASE` | 21000 | Base transaction cost |
| `TX_CREATE` | 32000 | Additional cost for contract creation tx |
| `TX_DATA_PER_ZERO` | 4 | Per zero byte in tx data |
| `TX_DATA_PER_NON_ZERO` | 16 | Per non-zero byte in tx data |
| `TX_DATA_TOKEN_STANDARD` | 4 | Token cost per data element |
| `TX_DATA_TOKEN_FLOOR` | 0 | Minimum token cost |

## Call and Create

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `CALL_VALUE` | 9000 | Additional cost when transferring value |
| `CALL_STIPEND` | 2300 | Gas stipend for calls with value |
| `NEW_ACCOUNT` | 25000 | Creating a new account via call |
| `OPCODE_CREATE_BASE` | 32000 | CREATE opcode base cost |
| `CODE_DEPOSIT_PER_BYTE` | 200 | Per byte of deployed code |
| `CODE_INIT_PER_WORD` | 2 | Per word of init code (EIP-3860) |
| `OPCODE_SELFDESTRUCT_BASE` | 5000 | SELFDESTRUCT base cost |

## Auth (EIP-3074)

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `AUTH_PER_EMPTY_ACCOUNT` | 25000 | AUTH cost for empty account |

## Precompile Costs

| GasCosts Field | Typical Value | Precompile |
|---|---|---|
| `PRECOMPILE_ECRECOVER` | 3000 | ecRecover (0x01) |
| `PRECOMPILE_SHA256_BASE` | 60 | SHA-256 base (0x02) |
| `PRECOMPILE_SHA256_PER_WORD` | 12 | SHA-256 per word (0x02) |
| `PRECOMPILE_RIPEMD160_BASE` | 600 | RIPEMD-160 base (0x03) |
| `PRECOMPILE_RIPEMD160_PER_WORD` | 120 | RIPEMD-160 per word (0x03) |
| `PRECOMPILE_IDENTITY_BASE` | 15 | Identity base (0x04) |
| `PRECOMPILE_IDENTITY_PER_WORD` | 3 | Identity per word (0x04) |
| `PRECOMPILE_ECADD` | 150 | BN256 add (0x06) |
| `PRECOMPILE_ECMUL` | 6000 | BN256 mul (0x07) |
| `PRECOMPILE_ECPAIRING_BASE` | 45000 | BN256 pairing base (0x08) |
| `PRECOMPILE_ECPAIRING_PER_POINT` | 34000 | BN256 pairing per point (0x08) |
| `PRECOMPILE_BLAKE2F_BASE` | 0 | BLAKE2 base (0x09) |
| `PRECOMPILE_BLAKE2F_PER_ROUND` | 1 | BLAKE2 per round (0x09) |
| `PRECOMPILE_POINT_EVALUATION` | 50000 | Point evaluation (0x0a) |
| `PRECOMPILE_BLS_G1ADD` | 500 | BLS G1 add (0x0b) |
| `PRECOMPILE_BLS_G1MUL` | 12000 | BLS G1 mul (0x0c) |
| `PRECOMPILE_BLS_G1MAP` | 5500 | BLS G1 map (0x12) |
| `PRECOMPILE_BLS_G2ADD` | 800 | BLS G2 add (0x0d) |
| `PRECOMPILE_BLS_G2MUL` | 45000 | BLS G2 mul (0x0e) |
| `PRECOMPILE_BLS_G2MAP` | 110000 | BLS G2 map (0x13) |
| `PRECOMPILE_BLS_PAIRING_BASE` | 115000 | BLS pairing base (0x11) |
| `PRECOMPILE_BLS_PAIRING_PER_PAIR` | 23000 | BLS pairing per pair (0x11) |
| `PRECOMPILE_P256VERIFY` | 6900 | P256 verify (0x100) |

## Block Access Lists

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `BLOCK_ACCESS_LIST_ITEM` | 2000 | Per-item cost for block access list entries (EIP-7928) |

## Refund Constants

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `REFUND_STORAGE_CLEAR` | 4800 | Refund for clearing a storage slot |
| `REFUND_AUTH_PER_EXISTING_ACCOUNT` | 25000 | AUTH refund for existing account |

## Opcode-Specific Fields

Each opcode has a dedicated `OPCODE_<NAME>` field. By default it equals the
opcode's tier value (see Base Operation Costs), but repricing it changes only
that opcode — so opcodes sharing a tier can be repriced independently. Values
below are typical (Osaka); exact values vary by fork, so `uv run gas-map` is the
authoritative source.

### Static opcodes

| GasCosts Field | Typical Value | Opcode |
|---|---|---|
| `OPCODE_ADD` | 3 | ADD |
| `OPCODE_SUB` | 3 | SUB |
| `OPCODE_MUL` | 5 | MUL |
| `OPCODE_DIV` | 5 | DIV |
| `OPCODE_SDIV` | 5 | SDIV |
| `OPCODE_MOD` | 5 | MOD |
| `OPCODE_SMOD` | 5 | SMOD |
| `OPCODE_ADDMOD` | 8 | ADDMOD |
| `OPCODE_MULMOD` | 8 | MULMOD |
| `OPCODE_SIGNEXTEND` | 5 | SIGNEXTEND |
| `OPCODE_LT` | 3 | LT |
| `OPCODE_GT` | 3 | GT |
| `OPCODE_SLT` | 3 | SLT |
| `OPCODE_SGT` | 3 | SGT |
| `OPCODE_EQ` | 3 | EQ |
| `OPCODE_ISZERO` | 3 | ISZERO |
| `OPCODE_AND` | 3 | AND |
| `OPCODE_OR` | 3 | OR |
| `OPCODE_XOR` | 3 | XOR |
| `OPCODE_NOT` | 3 | NOT |
| `OPCODE_BYTE` | 3 | BYTE |
| `OPCODE_SHL` | 3 | SHL |
| `OPCODE_SHR` | 3 | SHR |
| `OPCODE_SAR` | 3 | SAR |
| `OPCODE_CLZ` | 5 | CLZ |
| `OPCODE_CALLDATALOAD` | 3 | CALLDATALOAD |
| `OPCODE_COINBASE` | 2 | COINBASE |
| `OPCODE_BLOCKHASH` | 20 | BLOCKHASH |
| `OPCODE_BLOBHASH` | 3 | BLOBHASH |
| `OPCODE_JUMP` | 8 | JUMP |
| `OPCODE_JUMPI` | 10 | JUMPI |
| `OPCODE_JUMPDEST` | 1 | JUMPDEST |
| `OPCODE_PUSH` | 3 | PUSH1–PUSH32 |
| `OPCODE_DUP` | 3 | DUP1–DUP16 |
| `OPCODE_SWAP` | 3 | SWAP1–SWAP16 |

### Dynamic opcode base components

These set the base/per-unit cost of opcodes whose total cost also depends on
runtime context (memory expansion, data length, etc.).

| GasCosts Field | Typical Value | Opcode / Notes |
|---|---|---|
| `OPCODE_MLOAD_BASE` | 3 | MLOAD base |
| `OPCODE_MSTORE_BASE` | 3 | MSTORE base |
| `OPCODE_MSTORE8_BASE` | 3 | MSTORE8 base |
| `OPCODE_CALLDATACOPY_BASE` | 3 | CALLDATACOPY base |
| `OPCODE_CODECOPY_BASE` | 3 | CODECOPY base |
| `OPCODE_RETURNDATACOPY_BASE` | 3 | RETURNDATACOPY base |
| `OPCODE_MCOPY_BASE` | 3 | MCOPY base |
| `OPCODE_COPY_PER_WORD` | 3 | Per-word cost for copy opcodes |
| `OPCODE_CREATE_BASE` | 32000 | CREATE / CREATE2 base |
| `OPCODE_SELFDESTRUCT_BASE` | 5000 | SELFDESTRUCT base |
| `OPCODE_EXP_BASE` | 10 | EXP base |
| `OPCODE_EXP_PER_BYTE` | 50 | EXP per exponent byte |
| `OPCODE_KECCAK256_BASE` | 30 | KECCAK256 (SHA3) base |
| `OPCODE_KECCACK256_PER_WORD` | 6 | KECCAK256 (SHA3) per word (note: field name is misspelled in source) |
| `OPCODE_LOG_BASE` | 375 | LOG0–LOG4 base |
| `OPCODE_LOG_DATA_PER_BYTE` | 8 | LOG per data byte |
| `OPCODE_LOG_TOPIC` | 375 | LOG per topic |

## Dynamic Opcodes

Some opcodes have dynamic gas costs that depend on multiple `GasCosts` fields
and runtime context:

| Opcode | Relevant GasCosts Fields | Notes |
|---|---|---|
| EXP | `OPCODE_EXP_BASE`, `OPCODE_EXP_PER_BYTE` | Cost depends on exponent size |
| SLOAD | `WARM_SLOAD`, `COLD_STORAGE_ACCESS` | Warm vs cold access |
| SSTORE | `STORAGE_SET`, `STORAGE_RESET`, `WARM_SLOAD`, `COLD_STORAGE_ACCESS` | Complex rules based on original/current/new values |
| SHA3 | `OPCODE_KECCAK256_BASE`, `OPCODE_KECCACK256_PER_WORD` | Base + per-word cost |
| LOG0-LOG4 | `OPCODE_LOG_BASE`, `OPCODE_LOG_DATA_PER_BYTE`, `OPCODE_LOG_TOPIC` | Base + data + topics |
| CALL/CALLCODE | `WARM_ACCESS`, `COLD_ACCOUNT_ACCESS`, `CALL_VALUE`, `NEW_ACCOUNT` | Complex rules based on account state |
| CREATE/CREATE2 | `OPCODE_CREATE_BASE`, `CODE_INIT_PER_WORD` | Base + init code cost |
| BALANCE/EXTCODESIZE | `WARM_ACCESS`, `COLD_ACCOUNT_ACCESS` | Warm vs cold access |
| SELFDESTRUCT | `OPCODE_SELFDESTRUCT_BASE`, `COLD_ACCOUNT_ACCESS`, `NEW_ACCOUNT` | Depends on target account state |

## Generating Up-to-Date Mappings

The tables above reflect typical values. Exact values vary by fork.

For the authoritative mapping for a specific fork:

```bash
# Full mapping
uv run gas-map --fork Osaka

# Single opcode detail
uv run gas-map --opcode SLOAD --fork Osaka
```
