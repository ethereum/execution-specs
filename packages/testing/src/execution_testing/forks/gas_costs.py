"""Defines the data class that will contain gas cost constants on each fork."""

from dataclasses import dataclass

# Common Gas Cost Tiers
BASE = 2
VERY_LOW = 3
LOW = 5
MID = 8
HIGH = 10


@dataclass(kw_only=True, frozen=True)
class GasCosts:
    """Class that contains the gas cost constants for any fork."""

    # Tiers
    BASE: int
    VERY_LOW: int
    LOW: int
    MID: int
    HIGH: int

    # Access
    WARM_ACCESS: int
    COLD_ACCOUNT_ACCESS: int
    WARM_SLOAD: int
    COLD_STORAGE_ACCESS: int

    # Storage
    STORAGE_SET: int
    COLD_STORAGE_WRITE: int
    STORAGE_RESET: int

    # Call
    CALL_VALUE: int
    CALL_STIPEND: int
    NEW_ACCOUNT: int

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE: int
    CODE_INIT_PER_WORD: int

    # Authorization
    AUTH_PER_EMPTY_ACCOUNT: int

    # Utility
    MEMORY_PER_WORD: int

    # Transactions
    TX_BASE: int
    TX_CREATE: int
    TX_DATA_PER_ZERO: int
    TX_DATA_PER_NON_ZERO: int
    TX_DATA_TOKEN_STANDARD: int
    TX_DATA_TOKEN_FLOOR: int
    TX_ACCESS_LIST_ADDRESS: int
    TX_ACCESS_LIST_STORAGE_KEY: int

    # Refunds
    REFUND_STORAGE_CLEAR: int
    REFUND_AUTH_PER_EXISTING_ACCOUNT: int

    # Precompiles
    PRECOMPILE_ECRECOVER: int
    PRECOMPILE_SHA256_BASE: int
    PRECOMPILE_SHA256_PER_WORD: int
    PRECOMPILE_RIPEMD160_BASE: int
    PRECOMPILE_RIPEMD160_PER_WORD: int
    PRECOMPILE_IDENTITY_BASE: int
    PRECOMPILE_IDENTITY_PER_WORD: int
    PRECOMPILE_ECADD: int
    PRECOMPILE_ECMUL: int
    PRECOMPILE_ECPAIRING_BASE: int
    PRECOMPILE_ECPAIRING_PER_POINT: int
    PRECOMPILE_BLAKE2F_BASE: int
    PRECOMPILE_BLAKE2F_PER_ROUND: int
    PRECOMPILE_POINT_EVALUATION: int
    PRECOMPILE_BLS_G1ADD: int
    PRECOMPILE_BLS_G1MUL: int
    PRECOMPILE_BLS_G1MAP: int
    PRECOMPILE_BLS_G2ADD: int
    PRECOMPILE_BLS_G2MUL: int
    PRECOMPILE_BLS_G2MAP: int
    PRECOMPILE_BLS_PAIRING_BASE: int
    PRECOMPILE_BLS_PAIRING_PER_PAIR: int
    PRECOMPILE_P256VERIFY: int

    # Block Access Lists
    BLOCK_ACCESS_LIST_ITEM: int

    # Opcodes
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
    OPCODE_BLOCKHASH: int
    OPCODE_COINBASE: int
    OPCODE_PUSH: int
    OPCODE_DUP: int
    OPCODE_SWAP: int

    # Dynamic Opcode Components
    OPCODE_CALLDATACOPY_BASE: int
    OPCODE_CODECOPY_BASE: int
    OPCODE_MLOAD_BASE: int
    OPCODE_MSTORE_BASE: int
    OPCODE_MSTORE8_BASE: int
    OPCODE_SELFDESTRUCT_BASE: int
    OPCODE_COPY_PER_WORD: int
    OPCODE_CREATE_BASE: int
    OPCODE_EXP_BASE: int
    OPCODE_EXP_PER_BYTE: int
    OPCODE_LOG_BASE: int
    OPCODE_LOG_DATA_PER_BYTE: int
    OPCODE_LOG_TOPIC: int
    OPCODE_KECCAK256_BASE: int
    OPCODE_KECCACK256_PER_WORD: int

    # Defined post-Frontier
    OPCODE_SHL: int = 0
    OPCODE_SHR: int = 0
    OPCODE_SAR: int = 0
    OPCODE_RETURNDATACOPY_BASE: int = 0
    OPCODE_BLOBHASH: int = 0
    OPCODE_MCOPY_BASE: int = 0
    OPCODE_CLZ: int = 0
