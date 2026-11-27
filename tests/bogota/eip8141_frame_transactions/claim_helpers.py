"""Claim and witness helpers for EIP-8141 frame transaction tests."""

from typing import Any, Dict, Optional

from execution_testing import EOA, Bytes, Claim, Hash, P256Signer

from .spec import Spec

DIGEST = Hash(b"\x01" * 32)
"""Explicit digest signed by the witnesses of explicit-`msg` claims."""

SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
"""Order of the secp256k1 curve."""

SECP256R1N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
"""Order of the NIST P-256 (secp256r1) curve."""

P256_SIGNER = P256Signer(1)
"""The NIST P-256 key `1`, signing the P256 claims of the tests."""

P256_SIGNATURE = bytes(P256_SIGNER.sign_message(DIGEST))
"""
A valid `P256_VERIFIER` witness over `DIGEST` by `P256_SIGNER`:
`r || s || qx || qy` with low `s`. Malformed witnesses tamper with its
words.
"""

P256_R, P256_S, P256_QX, P256_QY = (
    int.from_bytes(P256_SIGNATURE[start : start + 32], "big")
    for start in range(0, 128, 32)
)
"""The words of `P256_SIGNATURE`."""


def signed_digest_claim(private_key: Hash, **overrides: Any) -> Claim:
    """
    Return a `SECP256K1_VERIFIER` claim over `DIGEST` keyed by the
    address of `private_key`, whose witness `private_key` signs.

    Keyword arguments override the corresponding claim fields after
    signing, for variants that differ from a valid claim in a single
    field.
    """
    signer = EOA(key=private_key)
    claim = Claim(
        verifier=Spec.SECP256K1_VERIFIER,
        key=Bytes(signer),
        msg=Bytes(DIGEST),
        witness=signer.sign_message(DIGEST),
    )
    for field, value in overrides.items():
        setattr(claim, field, value)
    return claim


def with_tampered_components(
    claim: Claim,
    v: Optional[int] = None,
    r: Optional[int] = None,
    s: Optional[int] = None,
) -> Claim:
    """Replace components of a claim's `v || r || s` witness."""
    assert claim.witness is not None
    witness = bytes(claim.witness)
    claim.witness = Bytes(
        (bytes([v]) if v is not None else witness[0:1])
        + (r.to_bytes(32, "big") if r is not None else witness[1:33])
        + (s.to_bytes(32, "big") if s is not None else witness[33:65])
    )
    return claim


def high_s_complement(claim: Claim) -> Claim:
    """
    Rewrite a claim's witness into its high-`s` complement `(r, N - s)`,
    which is algebraically valid but rejected by the canonical-encoding
    rule.
    """
    assert claim.witness is not None
    witness = bytes(claim.witness)
    s = int.from_bytes(witness[33:65], "big")
    return with_tampered_components(claim, v=witness[0] ^ 1, s=SECP256K1N - s)


def resized_witness(claim: Claim, length: int) -> Claim:
    """Truncate or zero-pad a claim's witness to `length` bytes."""
    assert claim.witness is not None
    witness = bytes(claim.witness)
    claim.witness = Bytes(witness[:length].ljust(length, b"\x00"))
    return claim


def valid_p256_claim(**components: int) -> Claim:
    """
    Return the `P256_VERIFIER` claim over `DIGEST` keyed by
    `P256_SIGNER`, with a witness built from `P256_SIGNATURE`'s words and
    the given components replaced, for variants that break the rule on
    one component and nothing else.
    """
    words = dict(r=P256_R, s=P256_S, qx=P256_QX, qy=P256_QY)
    words.update(components)
    return p256_claim(**words, key=Bytes(P256_SIGNER))


def p256_claim(
    r: int, s: int, qx: int = 0, qy: int = 0, **overrides: Any
) -> Claim:
    """
    Return a `P256_VERIFIER` claim over `DIGEST` with a witness of the
    given signature components.

    Keyword arguments override the corresponding claim fields, for
    variants that differ in a single field.
    """
    fields: Dict[str, Any] = dict(
        verifier=Spec.P256_VERIFIER,
        msg=Bytes(DIGEST),
        witness=Bytes(
            b"".join(value.to_bytes(32, "big") for value in (r, s, qx, qy))
        ),
    )
    fields.update(overrides)
    return Claim(**fields)


def canonical_claim(account: EOA, **overrides: Any) -> Claim:
    """
    Return a `SECP256K1_VERIFIER` claim over the canonical hash keyed by
    `account`'s address, sender or not, whose witness `account` signs;
    keyword arguments override single fields.
    """
    fields: Dict[str, Any] = dict(signer=account)
    fields.update(overrides)
    return Claim(**fields)


def sender_claim(sender: EOA) -> Claim:
    """
    Return the claim a sender holding a key carries by default: a
    `SECP256K1_VERIFIER` claim over the canonical hash with an empty key,
    which resolves to the sender.
    """
    return Claim(verifier=Spec.SECP256K1_VERIFIER, signed_by=sender)
