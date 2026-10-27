"""Signature entry helpers for EIP-8141 frame transaction tests."""

import hashlib
import hmac
from typing import Any, Dict, Optional, Tuple

from execution_testing import EOA, Bytes, FrameSignature, Hash, keccak256

from .spec import Spec

DIGEST = Hash(b"\x01" * 32)
"""Explicit digest signed by protocol-validated signature entries."""

SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
"""Order of the secp256k1 curve."""

SECP256R1N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
"""Order of the NIST P-256 (secp256r1) curve."""

P256_SIGNATURE = bytes.fromhex(
    "344372728b2e7d992e76fc836b134606b3ed88ad8934c020aa8946b90fc09a4f"
    "1695256f5464dda72bfbd6cb0d3fd89ca7380da0e476cbb5d94dc1507b77a88d"
    "6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296"
    "4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5"
)
"""
A valid P256 signature payload over `DIGEST`: `r || s || qx || qy`
with low `s`, produced with the NIST P-256 private key `1`. Kept as
the literal vector the released fixtures were filled with; new vectors
are derived deterministically with `p256_sign`.
"""

P256_R, P256_S, P256_QX, P256_QY = (
    int.from_bytes(P256_SIGNATURE[start : start + 32], "big")
    for start in range(0, 128, 32)
)
"""The words of `P256_SIGNATURE`."""

P256_SIGNER = Bytes(keccak256(P256_SIGNATURE[64:128])[12:])
"""The signer `P256_SIGNATURE`'s public key words hash to."""


def signed_digest_entry(key: Hash, **overrides: Any) -> FrameSignature:
    """
    Return a secp256k1 signature entry over `DIGEST` signed with `key`.

    Keyword arguments override the corresponding entry fields after
    signing, for variants that differ from a valid entry in a single
    field.
    """
    entry = FrameSignature(scheme=Spec.SCHEME_SECP256K1, msg=Bytes(DIGEST))
    entry.signed_over(bytes(DIGEST), key)
    for field, value in overrides.items():
        setattr(entry, field, value)
    return entry


def with_tampered_components(
    entry: FrameSignature,
    v: Optional[int] = None,
    r: Optional[int] = None,
    s: Optional[int] = None,
) -> FrameSignature:
    """Replace components of an entry's `v || r || s` signature."""
    sig = bytes(entry.signature)
    entry.signature = Bytes(
        (bytes([v]) if v is not None else sig[0:1])
        + (r.to_bytes(32, "big") if r is not None else sig[1:33])
        + (s.to_bytes(32, "big") if s is not None else sig[33:65])
    )
    return entry


def high_s_complement(entry: FrameSignature) -> FrameSignature:
    """
    Rewrite an entry's signature into its high-`s` complement
    `(r, N - s)`, which is algebraically valid but rejected by the
    protocol's canonical-encoding rule.
    """
    sig = bytes(entry.signature)
    s = int.from_bytes(sig[33:65], "big")
    return with_tampered_components(entry, v=sig[0] ^ 1, s=SECP256K1N - s)


def resized_signature(entry: FrameSignature, length: int) -> FrameSignature:
    """Truncate or zero-pad an entry's signature to `length` bytes."""
    sig = bytes(entry.signature)
    entry.signature = Bytes(sig[:length].ljust(length, b"\x00"))
    return entry


def valid_p256_entry(**components: int) -> FrameSignature:
    """
    Return the P256 signature entry over `DIGEST` built from
    `P256_SIGNATURE`'s words and the signer they hash to, with the
    given components replaced, for variants that break the rule on one
    component and nothing else.
    """
    words = dict(r=P256_R, s=P256_S, qx=P256_QX, qy=P256_QY)
    words.update(components)
    return p256_entry(**words, signer=P256_SIGNER)


def p256_entry(
    r: int, s: int, qx: int = 0, qy: int = 0, **overrides: Any
) -> FrameSignature:
    """
    Return a P256 signature entry over `DIGEST` with the given
    signature components.

    Keyword arguments override the corresponding entry fields, for
    variants that differ in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        scheme=Spec.SCHEME_P256,
        msg=Bytes(DIGEST),
        signature=Bytes(
            b"".join(value.to_bytes(32, "big") for value in (r, s, qx, qy))
        ),
    )
    kwargs.update(overrides)
    return FrameSignature(**kwargs)


def canonical_entry(account: EOA, **overrides: Any) -> FrameSignature:
    """
    Return a secp256k1 entry over the canonical signature hash, with
    `account` as its explicit signer and its key signing it when the
    transaction is signed, whether or not `account` sends it.

    Keyword arguments override the corresponding entry fields, for
    variants that differ from the canonical entry in a single field.
    """
    fields: Dict[str, Any] = dict(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(account),
        secret_key=account.key,
    )
    fields.update(overrides)
    return FrameSignature(**fields)


SECP256R1P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
"""Prime of the field the NIST P-256 (secp256r1) curve is defined over."""

SECP256R1A = SECP256R1P - 3
"""Coefficient `a` of the P-256 curve equation `y^2 = x^3 + a*x + b`."""

SECP256R1G = (
    0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
    0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
)
"""Generator of the P-256 group, as affine coordinates `(x, y)`."""

P256Point = Optional[Tuple[int, int]]
"""An affine P-256 point, with `None` the point at infinity."""


def p256_add(p: P256Point, q: P256Point) -> P256Point:
    """Return the sum of two P-256 points."""
    if p is None:
        return q
    if q is None:
        return p
    (x1, y1), (x2, y2) = p, q
    if x1 == x2 and (y1 + y2) % SECP256R1P == 0:
        return None
    if p == q:
        slope = (3 * x1 * x1 + SECP256R1A) * pow(2 * y1, -1, SECP256R1P)
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, SECP256R1P)
    x3 = (slope * slope - x1 - x2) % SECP256R1P
    return x3, (slope * (x1 - x3) - y1) % SECP256R1P


def p256_multiply(scalar: int, point: P256Point = SECP256R1G) -> P256Point:
    """Return `scalar * point`, the generator by default."""
    result: P256Point = None
    while scalar:
        if scalar & 1:
            result = p256_add(result, point)
        point = p256_add(point, point)
        scalar >>= 1
    return result


def p256_public_key(private_key: int) -> Tuple[int, int]:
    """Return the public key words `(qx, qy)` of a P-256 private key."""
    point = p256_multiply(private_key)
    assert point is not None, "the private key is a multiple of the order"
    return point


def rfc6979_nonce(digest: bytes, private_key: int) -> int:
    """
    Return the P-256 signing nonce RFC 6979 (§3.2) derives from
    `private_key` and `digest` with HMAC-SHA256.
    """
    key = private_key.to_bytes(32, "big")
    message = (int.from_bytes(digest, "big") % SECP256R1N).to_bytes(32, "big")
    v, k = b"\x01" * 32, b"\x00" * 32
    for separator in (b"\x00", b"\x01"):
        k = hmac.new(k, v + separator + key + message, hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()
    while True:
        v = hmac.new(k, v, hashlib.sha256).digest()
        nonce = int.from_bytes(v, "big")
        if 0 < nonce < SECP256R1N:
            return nonce
        k = hmac.new(k, v + b"\x00", hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()


def p256_sign(
    digest: bytes, private_key: int, nonce: Optional[int] = None
) -> Tuple[int, int]:
    """
    Return the P-256 ECDSA signature `(r, s)` of the 32-byte `digest`
    under `private_key`, with `s` normalized to the low half of the
    order.

    The nonce is `nonce` when given, for a vector built around a chosen
    nonce, and otherwise the RFC 6979 one, so the signature, and every
    fixture holding it, is the same on every fill. The arithmetic is
    plain Python, so signing does not depend on the OpenSSL build.
    """
    assert len(digest) == 32, "a P256 entry signs a 32-byte digest"
    if nonce is None:
        nonce = rfc6979_nonce(digest, private_key)
    point = p256_multiply(nonce)
    assert point is not None, "the nonce is a multiple of the order"
    r = point[0] % SECP256R1N
    z = int.from_bytes(digest, "big")
    s = pow(nonce, -1, SECP256R1N) * (z + r * private_key) % SECP256R1N
    assert r != 0 and s != 0, "the nonce yields a degenerate signature"
    return r, min(s, SECP256R1N - s)
