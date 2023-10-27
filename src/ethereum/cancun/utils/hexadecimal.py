"""
Utility Functions For Hexadecimal Strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Hexadecimal utility functions used in this specification, specific to
Cancun types.
"""
from ethereum.utils.hexadecimal import remove_hex_prefix

from ..fork_types import Address, Bloom, Root


def hex_to_root(hex_string: str) -> Root:
    """
    Convert hex string to trie root.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to trie root.

    Returns
    -------
    root : `Root`
        Trie root obtained from the given hexadecimal string.
    """
    return Root(bytes.fromhex(remove_hex_prefix(hex_string)))


def hex_to_bloom(hex_string: str) -> Bloom:
    """
    Convert hex string to bloom.

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to bloom.

    Returns
    -------
    bloom : `Bloom`
        Bloom obtained from the given hexadecimal string.
    """
    return Bloom(bytes.fromhex(remove_hex_prefix(hex_string)))


def hex_to_address(hex_string: str) -> Address:
    """
    Convert hex string to Address (20 bytes).

    Parameters
    ----------
    hex_string :
        The hexadecimal string to be converted to Address.

    Returns
    -------
    address : `Address`
        The address obtained from the given hexadecimal string.
    """
    return Address(bytes.fromhex(remove_hex_prefix(hex_string).rjust(40, "0")))
