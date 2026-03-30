"""Defines the data class that will contain gas cost constants on each fork."""

from dataclasses import dataclass

# Common Gas Cost Tiers
GAS_VERY_LOW = 3
GAS_LOW = 5
GAS_MID = 8
GAS_HIGH = 10


@dataclass(kw_only=True, frozen=True)
class GasCosts:
    """Class that contains the gas cost constants for any fork."""

    GAS_BASE: int
    GAS_VERY_LOW: int
    GAS_LOW: int
    GAS_MID: int
    GAS_HIGH: int
    GAS_WARM_ACCESS: int
    GAS_COLD_ACCOUNT_ACCESS: int
    GAS_TX_ACCESS_LIST_ADDRESS: int
    GAS_TX_ACCESS_LIST_STORAGE_KEY: int
    GAS_WARM_SLOAD: int
    GAS_COLD_STORAGE_ACCESS: int
    GAS_STORAGE_SET: int
    GAS_COLD_STORAGE_WRITE: int
    GAS_STORAGE_RESET: int

    GAS_SELF_DESTRUCT: int
    GAS_CREATE: int

    GAS_CODE_DEPOSIT_PER_BYTE: int
    GAS_CODE_INIT_PER_WORD: int

    GAS_CALL_VALUE: int
    GAS_CALL_STIPEND: int
    GAS_NEW_ACCOUNT: int

    GAS_EXPONENTIATION: int
    GAS_EXPONENTIATION_PER_BYTE: int

    GAS_MEMORY: int
    GAS_TX_BASE: int
    GAS_TX_CREATE: int
    GAS_TX_DATA_PER_ZERO: int
    GAS_TX_DATA_PER_NON_ZERO: int
    GAS_TX_DATA_TOKEN_STANDARD: int
    GAS_TX_DATA_TOKEN_FLOOR: int

    GAS_LOG: int
    GAS_LOG_DATA_PER_BYTE: int
    GAS_LOG_TOPIC: int

    GAS_KECCAK256: int
    GAS_KECCAK256_PER_WORD: int

    GAS_COPY: int

    GAS_AUTH_PER_EMPTY_ACCOUNT: int

    # Precompiled contract gas constants
    GAS_PRECOMPILE_ECRECOVER: int
    GAS_PRECOMPILE_SHA256_BASE: int
    GAS_PRECOMPILE_SHA256_PER_WORD: int
    GAS_PRECOMPILE_RIPEMD160_BASE: int
    GAS_PRECOMPILE_RIPEMD160_PER_WORD: int
    GAS_PRECOMPILE_IDENTITY_BASE: int
    GAS_PRECOMPILE_IDENTITY_PER_WORD: int

    GAS_PRECOMPILE_ECADD: int
    GAS_PRECOMPILE_ECMUL: int
    GAS_PRECOMPILE_ECPAIRING_BASE: int
    GAS_PRECOMPILE_ECPAIRING_PER_POINT: int

    GAS_PRECOMPILE_BLAKE2F_BASE: int
    GAS_PRECOMPILE_BLAKE2F_PER_ROUND: int

    GAS_PRECOMPILE_POINT_EVALUATION: int

    GAS_PRECOMPILE_BLS_G1ADD: int
    GAS_PRECOMPILE_BLS_G1MUL: int
    GAS_PRECOMPILE_BLS_G1MAP: int
    GAS_PRECOMPILE_BLS_G2ADD: int
    GAS_PRECOMPILE_BLS_G2MUL: int
    GAS_PRECOMPILE_BLS_G2MAP: int
    GAS_PRECOMPILE_BLS_PAIRING_BASE: int
    GAS_PRECOMPILE_BLS_PAIRING_PER_PAIR: int

    GAS_PRECOMPILE_P256VERIFY: int

    # Refund constants
    REFUND_STORAGE_CLEAR: int
    REFUND_AUTH_PER_EXISTING_ACCOUNT: int

    GAS_BLOCK_ACCESS_LIST_ITEM: int

    # Opcode specific gas constants for repricing
    OPCODE_ADD: int
    OPCODE_SUB: int
    OPCODE_MUL: int
    OPCODE_DIV: int
    OPCODE_SDIV: int
    OPCODE_MOD: int
    OPCODE_SMOD: int
    OPCODE_ADDMOD: int
    OPCODE_MULMOD: int
    OPCODE_SIGNEXTEND: int
    OPCODE_LT: int
    OPCODE_GT: int
    OPCODE_SLT: int
    OPCODE_SGT: int
    OPCODE_EQ: int
    OPCODE_ISZERO: int
    OPCODE_AND: int
    OPCODE_OR: int
    OPCODE_XOR: int
    OPCODE_NOT: int
    OPCODE_BYTE: int
    OPCODE_JUMP: int
    OPCODE_JUMPI: int
    OPCODE_JUMPDEST: int
    OPCODE_CALLDATALOAD: int
    OPCODE_CALLDATACOPY: int
    OPCODE_CODECOPY: int
    OPCODE_BLOCKHASH: int
    OPCODE_MLOAD: int
    OPCODE_MSTORE: int
    OPCODE_MSTORE8: int
    OPCODE_PUSH: int
    OPCODE_DUP: int
    OPCODE_SWAP: int

    # Defined post-Frontier
    OPCODE_SHL: int = 0
    OPCODE_SHR: int = 0
    OPCODE_SAR: int = 0
    OPCODE_RETURNDATACOPY: int = 0
    OPCODE_BLOBHASH: int = 0
    OPCODE_MCOPY: int = 0
    OPCODE_CLZ: int = 0
