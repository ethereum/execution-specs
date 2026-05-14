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

from Crypto.Hash import keccak as _pycryptodome_keccak
from ethereum_types.bytes import Bytes32, Bytes64

Hash32 = Bytes32
Hash64 = Bytes64


def _hashlib_has_keccak() -> bool:
    """Return `True` if `hashlib` can compute pre-NIST Keccak digests."""
    try:
        hashlib.new("keccak-256", b"")
    except ValueError:
        return False
    return True


# Decide once at import time whether to dispatch to hashlib (linked OpenSSL)
# or to pycryptodome's bundled implementation. OpenSSL only gained
# default-provider Keccak in 3.2.0 (Nov 2023); LTS 3.0.x and 3.1.x (still
# shipped by Debian 12, RHEL 9, etc.) do not provide it. We probe with
# `hashlib.new()` because `hashlib.algorithms_available` omits some
# OpenSSL-provider digests on common builds (e.g. python-build-standalone /
# uv-managed CPython on OpenSSL 3.5.x), yielding false negatives.
_USE_HASHLIB = _hashlib_has_keccak()


if _USE_HASHLIB:

    def _keccak256_digest(buffer: bytes | bytearray) -> bytes:
        return hashlib.new("keccak-256", buffer).digest()

    def _keccak512_digest(buffer: bytes | bytearray) -> bytes:
        return hashlib.new("keccak-512", buffer).digest()
else:

    def _keccak256_digest(buffer: bytes | bytearray) -> bytes:
        return (
            _pycryptodome_keccak.new(digest_bits=256).update(buffer).digest()
        )

    def _keccak512_digest(buffer: bytes | bytearray) -> bytes:
        return (
            _pycryptodome_keccak.new(digest_bits=512).update(buffer).digest()
        )


def keccak256(buffer: bytes | bytearray) -> Hash32:
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
    return Hash32(_keccak256_digest(buffer))


def keccak512(buffer: bytes | bytearray) -> Hash64:
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
    return Hash64(_keccak512_digest(buffer))
