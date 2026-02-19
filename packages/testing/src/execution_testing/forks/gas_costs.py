"""Defines the data class that will contain gas cost constants on each fork."""

from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class GasCosts:
    """Class that contains the gas cost constants for any fork."""

    G_JUMPDEST: int
    G_BASE: int
    G_VERY_LOW: int
    G_LOW: int
    G_MID: int
    G_HIGH: int
    G_WARM_ACCOUNT_ACCESS: int
    G_COLD_ACCOUNT_ACCESS: int
    G_ACCESS_LIST_ADDRESS: int
    G_ACCESS_LIST_STORAGE: int
    G_WARM_SLOAD: int
    G_COLD_SLOAD: int
    G_STORAGE_SET: int
    G_STORAGE_UPDATE: int
    G_STORAGE_RESET: int

    R_STORAGE_CLEAR: int

    G_SELF_DESTRUCT: int
    G_CREATE: int

    G_CODE_DEPOSIT_BYTE: int
    G_INITCODE_WORD: int

    G_CALL_VALUE: int
    G_CALL_STIPEND: int
    G_NEW_ACCOUNT: int

    G_EXP: int
    G_EXP_BYTE: int

    G_MEMORY: int

    G_TX_DATA_ZERO: int
    G_TX_DATA_NON_ZERO: int
    G_TX_DATA_STANDARD_TOKEN_COST: int
    G_TX_DATA_FLOOR_TOKEN_COST: int

    G_TRANSACTION: int
    G_TRANSACTION_CREATE: int

    G_LOG: int
    G_LOG_DATA: int
    G_LOG_TOPIC: int

    G_KECCAK_256: int
    G_KECCAK_256_WORD: int

    G_COPY: int
    G_BLOCKHASH: int

    G_AUTHORIZATION: int

    # Precompiled contract gas constants

    G_PRECOMPILE_ECRECOVER: int
    G_PRECOMPILE_SHA256_BASE: int
    G_PRECOMPILE_SHA256_WORD: int
    G_PRECOMPILE_RIPEMD160_BASE: int
    G_PRECOMPILE_RIPEMD160_WORD: int
    G_PRECOMPILE_IDENTITY_BASE: int
    G_PRECOMPILE_IDENTITY_WORD: int

    G_PRECOMPILE_ECADD: int
    G_PRECOMPILE_ECMUL: int
    G_PRECOMPILE_ECPAIRING_BASE: int
    G_PRECOMPILE_ECPAIRING_PER_POINT: int

    G_PRECOMPILE_BLAKE2F_BASE: int
    G_PRECOMPILE_BLAKE2F_PER_ROUND: int

    G_PRECOMPILE_POINT_EVALUATION: int

    G_PRECOMPILE_BLS_G1ADD: int
    G_PRECOMPILE_BLS_G1MUL: int
    G_PRECOMPILE_BLS_G1MAP: int
    G_PRECOMPILE_BLS_G2ADD: int
    G_PRECOMPILE_BLS_G2MUL: int
    G_PRECOMPILE_BLS_G2MAP: int
    G_PRECOMPILE_BLS_PAIRING_BASE: int
    G_PRECOMPILE_BLS_PAIRING_PER_PAIR: int

    G_PRECOMPILE_P256VERIFY: int

    # Refund constants

    R_AUTHORIZATION_EXISTING_AUTHORITY: int
