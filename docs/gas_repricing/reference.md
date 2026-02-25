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
| `GAS_VERY_LOW` | 3 | ADD, SUB, CALLDATALOAD, LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, XOR, NOT, BYTE, SHL, SHR, SAR, SIGNEXTEND, PUSH1-PUSH32, DUP1-DUP16, SWAP1-SWAP16, MLOAD, MSTORE, MSTORE8 |
| `GAS_LOW` | 5 | MUL, DIV, SDIV, MOD, SMOD, CLZ |
| `GAS_MID` | 8 | ADDMOD, MULMOD, JUMP |
| `GAS_HIGH` | 10 | JUMPI |
| `GAS_BASE` | 2 | ADDRESS, ORIGIN, CALLER, CALLVALUE, CALLDATASIZE, CODESIZE, GASPRICE, COINBASE, TIMESTAMP, NUMBER, PREVRANDAO, GASLIMIT, POP, PC, MSIZE, GAS, RETURNDATASIZE, CHAINID, SELFBALANCE, BASEFEE, BLOBBASEFEE |
| `GAS_JUMPDEST` | 1 | JUMPDEST |
| `GAS_BLOCK_HASH` | 20 | BLOCKHASH |

## Storage Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_WARM_SLOAD` | 100 | SLOAD when slot is warm |
| `GAS_COLD_SLOAD` | 2100 | SLOAD when slot is cold |
| `GAS_STORAGE_SET` | 20000 | SSTORE: setting a slot from zero to non-zero |
| `GAS_STORAGE_UPDATE` | 2900 | SSTORE: updating existing non-zero slot |
| `GAS_STORAGE_RESET` | 2900 | SSTORE: resetting to original value |

## Account Access Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_WARM_ACCOUNT_ACCESS` | 100 | BALANCE, EXTCODESIZE, etc. when warm |
| `GAS_COLD_ACCOUNT_ACCESS` | 2600 | BALANCE, EXTCODESIZE, etc. when cold |
| `GAS_TX_ACCESS_LIST_ADDRESS` | 2400 | Per address in access list |
| `GAS_TX_ACCESS_LIST_STORAGE_KEY` | 1900 | Per storage key in access list |

## Exponentiation

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_EXPONENTIATION` | 10 | EXP base cost |
| `GAS_EXPONENTIATION_PER_BYTE` | 50 | EXP per byte of exponent |

## Memory and Copy

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_MEMORY` | 3 | Memory expansion cost coefficient |
| `GAS_COPY` | 3 | Per-word copy cost (CALLDATACOPY, CODECOPY, etc.) |
| `GAS_KECCAK256` | 30 | SHA3 base cost |
| `GAS_KECCAK256_PER_WORD` | 6 | SHA3 per 32-byte word |

## Logging

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_LOG` | 375 | LOG base cost |
| `GAS_LOG_DATA_PER_BYTE` | 8 | LOG per byte of data |
| `GAS_LOG_TOPIC` | 375 | LOG per topic |

## Transaction Costs

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_TX_BASE` | 21000 | Base transaction cost |
| `GAS_TX_CREATE` | 32000 | Additional cost for contract creation tx |
| `GAS_TX_DATA_PER_ZERO` | 4 | Per zero byte in tx data |
| `GAS_TX_DATA_PER_NON_ZERO` | 16 | Per non-zero byte in tx data |
| `GAS_TX_DATA_TOKEN_STANDARD` | 4 | Token cost per data element |
| `GAS_TX_DATA_TOKEN_FLOOR` | 0 | Minimum token cost |

## Call and Create

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_CALL_VALUE` | 9000 | Additional cost when transferring value |
| `GAS_CALL_STIPEND` | 2300 | Gas stipend for calls with value |
| `GAS_NEW_ACCOUNT` | 25000 | Creating a new account via call |
| `GAS_CREATE` | 32000 | CREATE opcode base cost |
| `GAS_CODE_DEPOSIT_PER_BYTE` | 200 | Per byte of deployed code |
| `GAS_CODE_INIT_PER_WORD` | 2 | Per word of init code (EIP-3860) |
| `GAS_SELF_DESTRUCT` | 5000 | SELFDESTRUCT base cost |

## Auth (EIP-3074)

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `GAS_AUTH_PER_EMPTY_ACCOUNT` | 25000 | AUTH cost for empty account |

## Precompile Costs

| GasCosts Field | Typical Value | Precompile |
|---|---|---|
| `GAS_PRECOMPILE_ECRECOVER` | 3000 | ecRecover (0x01) |
| `GAS_PRECOMPILE_SHA256_BASE` | 60 | SHA-256 base (0x02) |
| `GAS_PRECOMPILE_SHA256_PER_WORD` | 12 | SHA-256 per word (0x02) |
| `GAS_PRECOMPILE_RIPEMD160_BASE` | 600 | RIPEMD-160 base (0x03) |
| `GAS_PRECOMPILE_RIPEMD160_PER_WORD` | 120 | RIPEMD-160 per word (0x03) |
| `GAS_PRECOMPILE_IDENTITY_BASE` | 15 | Identity base (0x04) |
| `GAS_PRECOMPILE_IDENTITY_PER_WORD` | 3 | Identity per word (0x04) |
| `GAS_PRECOMPILE_ECADD` | 150 | BN256 add (0x06) |
| `GAS_PRECOMPILE_ECMUL` | 6000 | BN256 mul (0x07) |
| `GAS_PRECOMPILE_ECPAIRING_BASE` | 45000 | BN256 pairing base (0x08) |
| `GAS_PRECOMPILE_ECPAIRING_PER_POINT` | 34000 | BN256 pairing per point (0x08) |
| `GAS_PRECOMPILE_BLAKE2F_BASE` | 0 | BLAKE2 base (0x09) |
| `GAS_PRECOMPILE_BLAKE2F_PER_ROUND` | 1 | BLAKE2 per round (0x09) |
| `GAS_PRECOMPILE_POINT_EVALUATION` | 50000 | Point evaluation (0x0a) |
| `GAS_PRECOMPILE_BLS_G1ADD` | 500 | BLS G1 add (0x0b) |
| `GAS_PRECOMPILE_BLS_G1MUL` | 12000 | BLS G1 mul (0x0c) |
| `GAS_PRECOMPILE_BLS_G1MAP` | 5500 | BLS G1 map (0x12) |
| `GAS_PRECOMPILE_BLS_G2ADD` | 800 | BLS G2 add (0x0d) |
| `GAS_PRECOMPILE_BLS_G2MUL` | 45000 | BLS G2 mul (0x0e) |
| `GAS_PRECOMPILE_BLS_G2MAP` | 110000 | BLS G2 map (0x13) |
| `GAS_PRECOMPILE_BLS_PAIRING_BASE` | 115000 | BLS pairing base (0x11) |
| `GAS_PRECOMPILE_BLS_PAIRING_PER_PAIR` | 23000 | BLS pairing per pair (0x11) |
| `GAS_PRECOMPILE_P256VERIFY` | 6900 | P256 verify (0x100) |

## Refund Constants

| GasCosts Field | Typical Value | Notes |
|---|---|---|
| `REFUND_STORAGE_CLEAR` | 4800 | Refund for clearing a storage slot |
| `REFUND_AUTH_PER_EXISTING_ACCOUNT` | 25000 | AUTH refund for existing account |

## Dynamic Opcodes

Some opcodes have dynamic gas costs that depend on multiple `GasCosts` fields
and runtime context:

| Opcode | Relevant GasCosts Fields | Notes |
|---|---|---|
| EXP | `GAS_EXPONENTIATION`, `GAS_EXPONENTIATION_PER_BYTE` | Cost depends on exponent size |
| SLOAD | `GAS_WARM_SLOAD`, `GAS_COLD_SLOAD` | Warm vs cold access |
| SSTORE | `GAS_STORAGE_SET`, `GAS_STORAGE_UPDATE`, `GAS_STORAGE_RESET`, `GAS_WARM_SLOAD`, `GAS_COLD_SLOAD` | Complex rules based on original/current/new values |
| SHA3 | `GAS_KECCAK256`, `GAS_KECCAK256_PER_WORD` | Base + per-word cost |
| LOG0-LOG4 | `GAS_LOG`, `GAS_LOG_DATA_PER_BYTE`, `GAS_LOG_TOPIC` | Base + data + topics |
| CALL/CALLCODE | `GAS_WARM_ACCOUNT_ACCESS`, `GAS_COLD_ACCOUNT_ACCESS`, `GAS_CALL_VALUE`, `GAS_NEW_ACCOUNT` | Complex rules based on account state |
| CREATE/CREATE2 | `GAS_CREATE`, `GAS_CODE_INIT_PER_WORD` | Base + init code cost |
| BALANCE/EXTCODESIZE | `GAS_WARM_ACCOUNT_ACCESS`, `GAS_COLD_ACCOUNT_ACCESS` | Warm vs cold access |
| SELFDESTRUCT | `GAS_SELF_DESTRUCT`, `GAS_COLD_ACCOUNT_ACCESS`, `GAS_NEW_ACCOUNT` | Depends on target account state |

## Generating Up-to-Date Mappings

The tables above reflect typical values. Exact values vary by fork.

For the authoritative mapping for a specific fork:

```bash
# Full mapping
uv run gas-map --fork Osaka

# Single opcode detail
uv run gas-map --opcode SLOAD --fork Osaka
```
