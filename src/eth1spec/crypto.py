"""
# Cryptographic Functions
"""

import coincurve
import sha3

from .eth_types import Bytes, Hash32, Hash64, Uint


def keccak256(bytes_: Bytes) -> Hash32:
    """
    Computes the keccak256 hash of the input `bytes_`.

    Parameters
    ----------
    bytes_ : `eth1spec.eth_types.Bytes`
        Input for the hashing function.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        Output of the hash function.
    """
    return sha3.keccak_256(bytes_).digest()


def keccak512(bytes_: Bytes) -> Hash64:
    """
    Computes the keccak512 hash of the input `bytes_`.

    Parameters
    ----------
    bytes_ : `eth1spec.eth_types.Bytes`
        Input for the hashing function.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        Output of the hash function.
    """
    return sha3.keccak_512(bytes_).digest()


def secp256k1_recover(r: Uint, s: Uint, v: Uint, msg_hash: Hash32) -> Bytes:
    """
    Recovers the public key from a given signature.

    Parameters
    ----------
    r : `eth1spec.number.Uint`
        TODO
    s : `eth1spec.number.Uint`
        TODO
    v : `eth1spec.number.Uint`
        TODO
    msg_hash : `eth1spec.eth_types.Hash32`
        Hash of the message being recovered.

    Returns
    -------
    public_key : `eth1spec.eth_types.Bytes`
        Recovered public key.
    """
    r_bytes = r.to_big_endian()
    s_bytes = s.to_big_endian()

    signature = bytearray([0] * 65)
    signature[32 - len(r_bytes) : 32] = r_bytes
    signature[64 - len(s_bytes) : 64] = s_bytes
    signature[64] = v
    public_key = coincurve.PublicKey.from_signature_and_message(
        signature, msg_hash, hasher=None
    )
    public_key = public_key.format(compressed=False)[1:]
    return public_key
