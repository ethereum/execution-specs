"""
Cryptographic Functions
^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Cryptographic primatives used in—but not defined by—the Ethereum specification.
"""

import coincurve
import sha3

from ..base_types import U256, Bytes, Bytes32, Bytes64

Hash32 = Bytes32
Hash64 = Bytes64

SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def keccak256(buffer: Bytes) -> Hash32:
    """
    Computes the keccak256 hash of the input `buffer`.

    Parameters
    ----------
    buffer :
        Input for the hashing function.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
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
    hash : `eth1spec.eth_types.Hash32`
        Output of the hash function.
    """
    return sha3.keccak_512(buffer).digest()


def secp256k1_recover(r: U256, s: U256, v: U256, msg_hash: Hash32) -> Bytes:
    """
    Recovers the public key from a given signature.

    Parameters
    ----------
    r :
        TODO
    s :
        TODO
    v :
        TODO
    msg_hash :
        Hash of the message being recovered.

    Returns
    -------
    public_key : `eth1spec.base_types.Bytes`
        Recovered public key.
    """
    r_bytes = r.to_be_bytes32()
    s_bytes = s.to_be_bytes32()

    signature = bytearray([0] * 65)
    signature[32 - len(r_bytes) : 32] = r_bytes
    signature[64 - len(s_bytes) : 64] = s_bytes
    signature[64] = v
    public_key = coincurve.PublicKey.from_signature_and_message(
        bytes(signature), msg_hash, hasher=None
    )
    public_key = public_key.format(compressed=False)[1:]
    return public_key
