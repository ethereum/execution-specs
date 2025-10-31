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
    TX_ACCESS_LIST_ADDRESS_COST: int
    TX_ACCESS_LIST_STORAGE_KEY_COST: int
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

    GAS_EXPONENTIATION: int
    GAS_EXPONENTIATION_PER_BYTE: int

    GAS_MEMORY: int

    G_TX_DATA_ZERO: int
    G_TX_DATA_NON_ZERO: int
    STANDARD_CALLDATA_TOKEN_COST: int
    FLOOR_CALLDATA_COST: int

    TX_BASE_COST: int
    TX_CREATE_COST: int

    GAS_LOG: int
    GAS_LOG_DATA: int
    GAS_LOG_TOPIC: int

    GAS_KECCAK256: int
    GAS_KECCAK256_WORD: int

    GAS_COPY: int
    GAS_BLOCK_HASH: int

    PER_EMPTY_ACCOUNT_COST: int

    PER_AUTH_BASE_COST: int
