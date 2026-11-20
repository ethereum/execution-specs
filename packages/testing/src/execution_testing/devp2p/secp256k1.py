"""
The secp256k1 operations required by the RLPx handshake.

Public keys and recoverable signatures come from `spec256k1`, which the
framework already uses for transactions. RLPx additionally needs a raw
Diffie-Hellman agreement (a point multiplication by a foreign public
key), which `spec256k1` does not expose, so it comes from
`cryptography` instead.
"""

from cryptography.hazmat.primitives.asymmetric import ec
from spec256k1 import PrivateKey


def public_key_bytes(private_key: bytes) -> bytes:
    """
    Return the 64 byte uncompressed public key for `private_key`.

    The leading `0x04` tag of the SEC encoding is stripped: RLPx carries
    public keys as bare coordinate pairs.
    """
    return PrivateKey(private_key).public_key.format(compressed=False)[1:]


def agree(private_key: bytes, public_key: bytes) -> bytes:
    """
    Return the 32 byte x coordinate of `private_key` times `public_key`.

    `public_key` is the 64 byte coordinate pair; a key of another length
    or off the curve raises `ValueError`.
    """
    if len(public_key) != 64:
        raise ValueError(f"public key is {len(public_key)} bytes, expected 64")
    curve = ec.SECP256K1()
    secret = ec.derive_private_key(int.from_bytes(private_key, "big"), curve)
    remote = ec.EllipticCurvePublicKey.from_encoded_point(
        curve, b"\x04" + public_key
    )
    return secret.exchange(ec.ECDH(), remote)
