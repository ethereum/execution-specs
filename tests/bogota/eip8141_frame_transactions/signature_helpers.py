"""Signature entry helpers for EIP-8141 frame transaction tests."""

from typing import Any, Dict, Optional

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
with low `s`, produced with the NIST P-256 private key `1`. Embedded
as a constant because P256 signing is randomized and fixtures must be
deterministic.
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
