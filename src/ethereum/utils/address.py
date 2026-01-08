"""
Utility Functions For Ethereum Addresses.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Address specific utility functions used across the Ethereum specification.
These functions provide common operations for working with Ethereum addresses,
including validation, checksumming, and conversions.
"""

from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256

# Standard Ethereum address length in bytes
ADDRESS_BYTE_LENGTH: int = 20

# Standard Ethereum address length in hex characters (without 0x prefix)
ADDRESS_HEX_LENGTH: int = 40


def is_valid_address_length(address: Bytes) -> bool:
    """
    Check if the given bytes have the correct length for an Ethereum address.

    An Ethereum address must be exactly 20 bytes long.

    Parameters
    ----------
    address :
        The byte string to validate.

    Returns
    -------
    is_valid : `bool`
        True if the address has the correct length, False otherwise.

    Examples
    --------
    >>> is_valid_address_length(b'\\x00' * 20)
    True
    >>> is_valid_address_length(b'\\x00' * 19)
    False

    """
    return len(address) == ADDRESS_BYTE_LENGTH


def is_zero_address(address: Bytes20) -> bool:
    """
    Check if the given address is the zero address (all zeros).

    The zero address is commonly used to represent contract creation
    transactions or as a burn address.

    Parameters
    ----------
    address :
        The 20-byte address to check.

    Returns
    -------
    is_zero : `bool`
        True if the address is all zeros, False otherwise.

    Examples
    --------
    >>> is_zero_address(Bytes20(b'\\x00' * 20))
    True

    """
    return address == Bytes20(b"\x00" * ADDRESS_BYTE_LENGTH)


def is_precompile_address(address: Bytes20, max_precompile: int = 10) -> bool:
    """
    Check if the given address is a precompiled contract address.

    Precompiled contracts are special addresses (typically 0x01 through 0x0a
    on mainnet) that contain built-in functionality like cryptographic
    operations.

    Parameters
    ----------
    address :
        The 20-byte address to check.
    max_precompile :
        The maximum precompile address number (inclusive).
        Default is 10 for post-Prague forks.

    Returns
    -------
    is_precompile : `bool`
        True if the address is a precompile, False otherwise.

    Examples
    --------
    >>> addr = Bytes20(b'\\x00' * 19 + b'\\x01')
    >>> is_precompile_address(addr)
    True

    """
    # Check if the first 19 bytes are zero
    if address[:19] != b"\x00" * 19:
        return False

    # Check if the last byte is within precompile range
    last_byte = address[19]
    return 1 <= last_byte <= max_precompile


def address_to_uint(address: Bytes20) -> Uint:
    """
    Convert an address to its unsigned integer representation.

    Parameters
    ----------
    address :
        The 20-byte address to convert.

    Returns
    -------
    value : `Uint`
        The unsigned integer value of the address.

    """
    return Uint.from_be_bytes(address)


def uint_to_address(value: Uint | U256) -> Bytes20:
    """
    Convert an unsigned integer to a 20-byte address.

    The integer is converted to big-endian bytes and the last 20 bytes
    are used as the address (truncating from the left if necessary).

    Parameters
    ----------
    value :
        The unsigned integer to convert.

    Returns
    -------
    address : `Bytes20`
        The 20-byte address representation.

    """
    return Bytes20(value.to_be_bytes32()[-ADDRESS_BYTE_LENGTH:])


def to_checksum_address(address: Bytes20) -> str:
    """
    Convert an address to its EIP-55 checksummed string representation.

    EIP-55 defines a method for encoding Ethereum addresses with
    mixed-case letters that serves as a checksum without increasing
    the length of the address.

    Parameters
    ----------
    address :
        The 20-byte address to convert.

    Returns
    -------
    checksummed : `str`
        The checksummed address string with '0x' prefix.

    See Also
    --------
    https://eips.ethereum.org/EIPS/eip-55

    Examples
    --------
    >>> addr = Bytes20(bytes.fromhex('5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed'))
    >>> to_checksum_address(addr)
    '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed'

    """
    hex_address = address.hex().lower()
    hash_hex = keccak256(hex_address.encode()).hex()

    checksummed = "0x"
    for i, char in enumerate(hex_address):
        if char in "0123456789":
            checksummed += char
        elif int(hash_hex[i], 16) >= 8:
            checksummed += char.upper()
        else:
            checksummed += char.lower()

    return checksummed


def is_valid_checksum_address(address_str: str) -> bool:
    """
    Validate that an address string has a valid EIP-55 checksum.

    Parameters
    ----------
    address_str :
        The address string to validate (with or without '0x' prefix).

    Returns
    -------
    is_valid : `bool`
        True if the checksum is valid, False otherwise.

    See Also
    --------
    https://eips.ethereum.org/EIPS/eip-55

    """
    # Remove 0x prefix if present
    if address_str.startswith("0x") or address_str.startswith("0X"):
        address_str = address_str[2:]

    # Must be exactly 40 hex characters
    if len(address_str) != ADDRESS_HEX_LENGTH:
        return False

    # Check if it's valid hex
    try:
        address_bytes = Bytes20(bytes.fromhex(address_str))
    except ValueError:
        return False

    # Get the expected checksummed version
    expected = to_checksum_address(address_bytes)[2:]  # Remove 0x prefix

    return address_str == expected
