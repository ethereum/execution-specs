"""
Cryptographic Hash Functions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Cryptographic hashing functions.
"""

import hashlib

from ethereum_types.bytes import Bytes, Bytes32, Bytes64

Hash32 = Bytes32
Hash64 = Bytes64


def keccak256(buffer: Bytes | bytearray) -> Hash32:
    """
    Computes the keccak256 hash of the input `buffer`.

    Parameters
    ----------
    buffer :
        Input for the hashing function.

    Returns
    -------
    hash : `ethereum.base_types.Hash32`
        Output of the hash function.

    """
    return Hash32(hashlib.new("keccak-256", buffer).digest())


def keccak512(buffer: Bytes | bytearray) -> Hash64:
    """
    Computes the keccak512 hash of the input `buffer`.

    Parameters
    ----------
    buffer :
        Input for the hashing function.

    Returns
    -------
    hash : `ethereum.base_types.Hash32`
        Output of the hash function.

    """
    return Hash64(hashlib.new("keccak-512", buffer).digest())
