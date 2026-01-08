"""
Utility Functions For Ethereum Data Validation.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Validation utility functions used across the Ethereum specification.
These functions provide common validation operations for Ethereum data types.
"""

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

# Maximum values for common Ethereum types
MAX_U64: int = 2**64 - 1
MAX_U256: int = 2**256 - 1

# Gas limits
MAX_GAS_LIMIT: int = 2**63 - 1

# Nonce limits (EIP-2681)
MAX_NONCE: int = 2**64 - 2

# Block number limits
MAX_BLOCK_NUMBER: int = 2**64 - 1


def is_valid_gas_limit(gas_limit: Uint | U256 | int) -> bool:
    """
    Check if a gas limit value is within valid bounds.

    Parameters
    ----------
    gas_limit :
        The gas limit value to validate.

    Returns
    -------
    is_valid : `bool`
        True if the gas limit is valid, False otherwise.

    Notes
    -----
    Gas limit must be positive and not exceed the maximum safe value.

    """
    gas_value = int(gas_limit)
    return 0 < gas_value <= MAX_GAS_LIMIT


def is_valid_nonce(nonce: Uint | U64 | int) -> bool:
    """
    Check if a nonce value is within valid bounds according to EIP-2681.

    Parameters
    ----------
    nonce :
        The nonce value to validate.

    Returns
    -------
    is_valid : `bool`
        True if the nonce is valid (less than 2**64 - 1), False otherwise.

    See Also
    --------
    https://eips.ethereum.org/EIPS/eip-2681

    Notes
    -----
    According to EIP-2681, the nonce must be strictly less than 2**64 - 1
    to allow for incrementing without overflow.

    """
    nonce_value = int(nonce)
    return 0 <= nonce_value <= MAX_NONCE


def is_valid_block_number(block_number: Uint | int) -> bool:
    """
    Check if a block number is within valid bounds.

    Parameters
    ----------
    block_number :
        The block number to validate.

    Returns
    -------
    is_valid : `bool`
        True if the block number is non-negative and within bounds.

    """
    block_value = int(block_number)
    return 0 <= block_value <= MAX_BLOCK_NUMBER


def is_valid_u256(value: int) -> bool:
    """
    Check if an integer value fits within U256 bounds.

    Parameters
    ----------
    value :
        The integer value to validate.

    Returns
    -------
    is_valid : `bool`
        True if the value is non-negative and less than 2**256.

    """
    return 0 <= value <= MAX_U256


def is_valid_u64(value: int) -> bool:
    """
    Check if an integer value fits within U64 bounds.

    Parameters
    ----------
    value :
        The integer value to validate.

    Returns
    -------
    is_valid : `bool`
        True if the value is non-negative and less than 2**64.

    """
    return 0 <= value <= MAX_U64


def is_valid_hash(hash_value: Bytes) -> bool:
    """
    Check if a byte sequence is a valid 32-byte hash.

    Parameters
    ----------
    hash_value :
        The byte sequence to validate.

    Returns
    -------
    is_valid : `bool`
        True if the value is exactly 32 bytes, False otherwise.

    """
    return len(hash_value) == 32


def is_zero_hash(hash_value: Bytes32) -> bool:
    """
    Check if a hash is the zero hash (all zeros).

    Parameters
    ----------
    hash_value :
        The 32-byte hash to check.

    Returns
    -------
    is_zero : `bool`
        True if the hash is all zeros, False otherwise.

    """
    return hash_value == Bytes32(b"\x00" * 32)


def is_valid_chain_id(chain_id: int) -> bool:
    """
    Check if a chain ID is valid according to EIP-2294.

    Parameters
    ----------
    chain_id :
        The chain ID to validate.

    Returns
    -------
    is_valid : `bool`
        True if the chain ID is positive and fits in uint64.

    See Also
    --------
    https://eips.ethereum.org/EIPS/eip-2294

    Notes
    -----
    Chain IDs must be positive integers. While there's no explicit upper
    bound defined, we use uint64 as a practical limit.

    """
    return 0 < chain_id <= MAX_U64


def validate_transaction_value(value: U256 | int) -> bool:
    """
    Check if a transaction value is valid.

    Parameters
    ----------
    value :
        The transaction value in wei.

    Returns
    -------
    is_valid : `bool`
        True if the value is non-negative and within U256 bounds.

    """
    int_value = int(value)
    return 0 <= int_value <= MAX_U256


def is_valid_base_fee(base_fee: U256 | int) -> bool:
    """
    Check if a base fee value is valid (post-London fork).

    Parameters
    ----------
    base_fee :
        The base fee per gas in wei.

    Returns
    -------
    is_valid : `bool`
        True if the base fee is positive and within U256 bounds.

    Notes
    -----
    Base fee must be at least 1 wei after the London fork (EIP-1559).

    """
    fee_value = int(base_fee)
    return 0 < fee_value <= MAX_U256
