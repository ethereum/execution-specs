"""
Cryptographic Hash Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Cryptographic hashing functions.
"""

import sha3

from ..base_types import Bytes, Bytes32, Bytes64

Hash32 = Bytes32
Hash64 = Bytes64


def keccak256(buffer: Bytes) -> Hash32:
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
    return sha3.keccak_256(buffer).digest()


def keccak512(buffer: Bytes) -> Hash64:
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
    return sha3.keccak_512(buffer).digest()
