"""Test deterministic P-256 signing."""

import hashlib

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    encode_dss_signature,
)
from cryptography.hazmat.primitives.hashes import SHA256

from ..p256 import SECP256R1N, P256Signature, p256_sign

DIGEST = b"\x01" * 32

# RFC 6979, A.2.5: P-256 key, message "sample" hashed with SHA-256.
RFC6979_D = 0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721
RFC6979_QX = 0x60FED4BA255A9D31C961EB74C6356D68C049B8923B61FA6CE669622E60F29FB6
RFC6979_QY = 0x7903FE1008B8BC99A41AE9E95628BC64F2F1B20C2D7E9F5177A3C294D4462299
RFC6979_R = 0xEFD48B2AACB6A8FD1140DD9CD45E81D69D2C877B56AAF991C34D0EA84EAF3716
RFC6979_S = 0xF7CB1C942D657C41D436C7A1B6E29F65F3E900DBB9AFF4064DC4AB2F843ACDA8

# The P-256 base point, which is the public key of private key 1.
GX = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
GY = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5


def verify(signature: P256Signature, digest: bytes) -> None:
    """Raise `InvalidSignature` unless `signature` verifies `digest`."""
    public_key = ec.EllipticCurvePublicNumbers(
        signature.qx, signature.qy, ec.SECP256R1()
    ).public_key()
    public_key.verify(
        encode_dss_signature(signature.r, signature.s),
        digest,
        ec.ECDSA(Prehashed(SHA256())),
    )


def test_rfc6979_vector() -> None:
    """Match RFC 6979, with `s` normalized to the lower half."""
    signature = p256_sign(hashlib.sha256(b"sample").digest(), RFC6979_D)
    assert signature == P256Signature(
        r=RFC6979_R,
        s=SECP256R1N - RFC6979_S,
        qx=RFC6979_QX,
        qy=RFC6979_QY,
    )


def test_deterministic() -> None:
    """Sign the same digest with the same key to the same signature."""
    assert p256_sign(DIGEST, 1) == p256_sign(DIGEST, 1)
    assert p256_sign(DIGEST, 1) != p256_sign(b"\x02" * 32, 1)


@pytest.mark.parametrize("key", [1, 2, RFC6979_D, SECP256R1N - 1])
def test_low_s_and_verifies(key: int) -> None:
    """Emit low `s` and a signature that verifies the digest."""
    signature = p256_sign(DIGEST, key)
    assert 0 < signature.s <= SECP256R1N // 2
    verify(signature, DIGEST)
    with pytest.raises(InvalidSignature):
        verify(signature, b"\x02" * 32)


def test_key_as_bytes() -> None:
    """Accept the key as 32 big-endian bytes."""
    assert p256_sign(DIGEST, (1).to_bytes(32, "big")) == p256_sign(DIGEST, 1)


def test_public_key_of_key_one_is_base_point() -> None:
    """Return the public key of the signing key."""
    signature = p256_sign(DIGEST, 1)
    assert (signature.qx, signature.qy) == (GX, GY)


def test_compatible_with_static_signature() -> None:
    """
    Agree with `P256_SIGNATURE` of the EIP-8141 tests, a signature over
    `DIGEST` with key 1 made by randomized signing: its nonce differs,
    so `r` and `s` differ, but the public key matches and both verify.
    """
    static = P256Signature(
        r=0x344372728B2E7D992E76FC836B134606B3ED88AD8934C020AA8946B90FC09A4F,
        s=0x1695256F5464DDA72BFBD6CB0D3FD89CA7380DA0E476CBB5D94DC1507B77A88D,
        qx=GX,
        qy=GY,
    )
    live = p256_sign(DIGEST, 1)
    assert (live.qx, live.qy) == (static.qx, static.qy)
    assert static.s <= SECP256R1N // 2
    verify(static, DIGEST)
    verify(live, DIGEST)


def test_bytes_layout() -> None:
    """Encode as `r || s || qx || qy`."""
    signature = p256_sign(DIGEST, 1)
    encoded = bytes(signature)
    assert len(encoded) == 128
    assert encoded[64:] == GX.to_bytes(32, "big") + GY.to_bytes(32, "big")
    assert int.from_bytes(encoded[:32], "big") == signature.r
    assert int.from_bytes(encoded[32:64], "big") == signature.s


@pytest.mark.parametrize("length", [0, 31, 33])
def test_rejects_digest_of_wrong_length(length: int) -> None:
    """Sign only 32-byte digests."""
    with pytest.raises(ValueError):
        p256_sign(b"\x01" * length, 1)
