"""Defines the data class that will contain gas cost constants on each fork."""

from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class GasCosts:
    """Class that contains the gas cost constants for any fork."""

    GAS_JUMPDEST: int
    GAS_BASE: int
    GAS_VERY_LOW: int
    GAS_LOW: int
    GAS_MID: int
    GAS_HIGH: int
    GAS_WARM_ACCESS: int
    GAS_COLD_ACCOUNT_ACCESS: int
    G_ACCESS_LIST_ADDRESS: int
    G_ACCESS_LIST_STORAGE: int
    GAS_WARM_ACCESS: int
    GAS_COLD_SLOAD: int
    GAS_STORAGE_SET: int
    GAS_STORAGE_UPDATE: int

    GAS_STORAGE_CLEAR_REFUND: int

    GAS_SELF_DESTRUCT: int
    GAS_CREATE: int

    GAS_CODE_DEPOSIT: int
    GAS_INIT_CODE_WORD_COST: int

    GAS_CALL_VALUE: int
    GAS_CALL_STIPEND: int
    GAS_NEW_ACCOUNT: int

    G_EXP: int
    G_EXP_BYTE: int

    GAS_MEMORY: int

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

    GAS_COPY: int
    G_BLOCKHASH: int

    G_AUTHORIZATION: int

    # Precompiled contract gas constants

    G_PRECOMPILE_ECADD: int = 0
    G_PRECOMPILE_ECMUL: int = 0
    G_PRECOMPILE_ECPAIRING_BASE: int = 0
    G_PRECOMPILE_ECPAIRING_PER_POINT: int = 0

    # Refund constants

    R_AUTHORIZATION_EXISTING_AUTHORITY: int
