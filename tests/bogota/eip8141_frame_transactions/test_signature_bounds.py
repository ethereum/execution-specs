"""
Signature validation boundary tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Every signature entry is validated before any frame runs, and one entry
that fails validation makes the whole transaction invalid (§Transaction
Signatures: "If any signature is malformed, or any protocol-validated
signature is invalid, the whole transaction is invalid."). The cases
here sit on the exact numeric boundaries of `validate_signature`
(§Signature Validation) and on the rules that bind a signature to its
signer and to its transaction, each built so that a client missing the
rule under test accepts the transaction.

The secp256k1 vectors below are fixed constants: a signature with
`r = Gx` (the generator's x-coordinate) over `DIGEST` recovers a
different public key for every `s` and recovery id, so a chosen `s`
determines its signer. Each signer was computed with plain ECDSA
public key recovery, `Q = r^-1 * (s * R - z * G)`, where `R` is the
curve point with x-coordinate `r` and the parity given by `v`.

Like the other static rules, every case fills as a state test, which
checks the verdict against the reference implementation, and as a
transaction test, which pins the verdict on the transaction alone; see
`test_static_validity.py` for why both formats are needed.
"""

from typing import Callable, List, Optional, Union

import pytest
from execution_testing import (
    EOA,
    SECP256K1_SIGNATURE_LENGTH,
    Account,
    Alloc,
    Bytes,
    FrameSignature,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionTestFiller,
    keccak256,
)

from .helpers import verify_frame
from .signature_helpers import (
    DIGEST,
    P256_SIGNATURE,
    P256_SIGNER,
    SECP256K1N,
    SECP256R1N,
    canonical_entry,
    p256_entry,
    p256_public_key,
    p256_sign,
    signed_digest_entry,
    with_tampered_components,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SECP256K1_GX = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
)
"""x-coordinate of the secp256k1 generator, used as `r`."""

SECP256K1_HALF_ORDER_SIGNER_V0 = Bytes(
    "0xd9b25053e1790082384dae367fed99cdcd7fb6cb"
)
"""
Signer recovered from `(v=0, r=Gx, s=SECP256K1N // 2)` over `DIGEST`.
Its high-`s` complement `(v=1, r=Gx, s=SECP256K1N // 2 + 1)` recovers
the same signer.
"""

SECP256K1_HALF_ORDER_SIGNER_V1 = Bytes(
    "0x940488cbd686a8deea38c50b77f1cbf6b4c0eca8"
)
"""Signer recovered from `(v=1, r=Gx, s=SECP256K1N // 2)` over `DIGEST`."""

SECP256K1_S_ZERO_SIGNER = Bytes("0x1c20d20b1fa38c4e38aede97a3f4dd7c3f31c7b0")
"""
Signer that plain recovery returns for `(v=0, r=Gx, s=0)` over
`DIGEST`: with `s = 0` the formula reduces to `-r^-1 * z * G`, a valid
public key.
"""

SECP256K1_R_ABOVE_ORDER = SECP256K1N + 2
"""
An `r` above the curve order that is still the x-coordinate of a
secp256k1 point, so recovery that takes `r` without the range check
finds a point instead of failing.
"""

SECP256K1_R_ABOVE_ORDER_SIGNER = Bytes(
    "0xf28a4ea5a1c5a2a33a0fb3adce8e5333b7c77c84"
)
"""
Signer that plain recovery returns for `(v=0, r=SECP256K1N + 2, s=5)`
over `DIGEST`, using `R = (SECP256K1N + 2, y)` and `r mod SECP256K1N`
as the scalar.
"""

KEY_RECOVERY_ID_0 = Hash(2)
"""A private key whose signature over `DIGEST` has recovery id 0."""

KEY_RECOVERY_ID_1 = Hash(1)
"""A private key whose signature over `DIGEST` has recovery id 1."""

P256_HALF_ORDER_KEY = (
    0x28236AD4A209D04E3B97653AD600F431C0C62C68290A9B25629ADD03577BAC65
)
"""
Private key of a P-256 signature over `DIGEST` whose `s` is exactly
`SECP256R1N // 2`. It was built by picking the nonce `k = 0x1234567`,
taking `r = x(k * G) mod n` and solving for the private key
`d = (s * k - z) * r^-1 mod n`.
"""

P256_HALF_ORDER_NONCE = 0x1234567
"""The nonce `k` the half-order signature was built from."""

P256_HALF_ORDER_R, P256_HALF_ORDER_S = p256_sign(
    bytes(DIGEST), P256_HALF_ORDER_KEY, nonce=P256_HALF_ORDER_NONCE
)
"""The half-order signature's components, signed over `DIGEST`."""
assert P256_HALF_ORDER_S == SECP256R1N // 2

P256_HALF_ORDER_QX, P256_HALF_ORDER_QY = p256_public_key(P256_HALF_ORDER_KEY)
"""The public key words of `P256_HALF_ORDER_KEY`."""

P256_HALF_ORDER_SIGNER = Bytes(
    keccak256(
        P256_HALF_ORDER_QX.to_bytes(32, "big")
        + P256_HALF_ORDER_QY.to_bytes(32, "big")
    )[12:]
)
"""The signer `P256_HALF_ORDER_QX || P256_HALF_ORDER_QY` hashes to."""


def secp256k1_vector(v: int, r: int, s: int, signer: Bytes) -> FrameSignature:
    """Return a secp256k1 entry over `DIGEST` with fixed components."""
    return FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=signer,
        msg=Bytes(DIGEST),
        signature=Bytes(
            bytes([v]) + r.to_bytes(32, "big") + s.to_bytes(32, "big")
        ),
    )


def recovery_id_entry(key: Hash, recovery_id: int) -> FrameSignature:
    """
    Return a valid entry over `DIGEST` signed with `key`, whose explicit
    signer is the key's address, after checking its recovery id.
    """
    entry = signed_digest_entry(key, signer=Bytes(EOA(key=key)))
    assert bytes(entry.signature)[0] == recovery_id
    return entry


def p256_valid_signature(**overrides: Bytes) -> FrameSignature:
    """
    Return a P256 entry carrying `P256_SIGNATURE`, which P256VERIFY
    accepts over `DIGEST`, with an empty signer unless overridden.
    """
    return FrameSignature(
        scheme=Spec.SCHEME_P256,
        msg=Bytes(DIGEST),
        signature=Bytes(P256_SIGNATURE),
        **overrides,
    )


def p256_half_order_entry(s: int) -> FrameSignature:
    """Return the half-order P-256 vector with the given `s`."""
    return p256_entry(
        r=P256_HALF_ORDER_R,
        s=s,
        qx=P256_HALF_ORDER_QX,
        qy=P256_HALF_ORDER_QY,
        signer=P256_HALF_ORDER_SIGNER,
    )


SIGNATURE_BOUND_CASES = [
    # secp256k1 `s` boundary (§Signature Validation:
    # "not (0 < s <= SECP256K1N // 2)").
    pytest.param(
        [
            secp256k1_vector(
                0,
                SECP256K1_GX,
                SECP256K1N // 2,
                SECP256K1_HALF_ORDER_SIGNER_V0,
            )
        ],
        None,
        id="secp256k1_s_half_order_v0",
    ),
    pytest.param(
        [
            secp256k1_vector(
                1,
                SECP256K1_GX,
                SECP256K1N // 2,
                SECP256K1_HALF_ORDER_SIGNER_V1,
            )
        ],
        None,
        id="secp256k1_s_half_order_v1",
    ),
    pytest.param(
        # The complement of `secp256k1_s_half_order_v0`: the same signer
        # recovers from it, so only the low-`s` bound rejects it.
        [
            secp256k1_vector(
                1,
                SECP256K1_GX,
                SECP256K1N // 2 + 1,
                SECP256K1_HALF_ORDER_SIGNER_V0,
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_s_half_order_plus_one",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Plain recovery accepts `s = 0` and returns this signer, so only
        # the lower bound of `s` rejects the entry.
        [secp256k1_vector(0, SECP256K1_GX, 0, SECP256K1_S_ZERO_SIGNER)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_s_zero_recoverable",
        marks=pytest.mark.exception_test,
    ),
    # secp256k1 `r` bound (§Signature Validation: "not (0 < r <
    # SECP256K1N)").
    pytest.param(
        [
            secp256k1_vector(
                0, SECP256K1_R_ABOVE_ORDER, 5, SECP256K1_R_ABOVE_ORDER_SIGNER
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_above_order_on_curve",
        marks=pytest.mark.exception_test,
    ),
    # secp256k1 recovery id (§Signature Validation: "v is the recovery
    # id (0 or 1)"). The explicit signer is the key's own address, so
    # the entry is rejected only for its `v` byte.
    pytest.param(
        [recovery_id_entry(KEY_RECOVERY_ID_0, 0)],
        None,
        id="secp256k1_v_0",
    ),
    pytest.param(
        [recovery_id_entry(KEY_RECOVERY_ID_1, 1)],
        None,
        id="secp256k1_v_1",
    ),
    pytest.param(
        # `v - 27` is the true recovery id, so a client that normalizes
        # the legacy encoding recovers the explicit signer.
        [
            with_tampered_components(
                recovery_id_entry(KEY_RECOVERY_ID_0, 0), v=27
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_27_true_signer",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            with_tampered_components(
                recovery_id_entry(KEY_RECOVERY_ID_1, 1), v=28
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_28_true_signer",
        marks=pytest.mark.exception_test,
    ),
    # P256 `s` boundary (§Signature Validation: "not (0 < s <=
    # SECP256R1N // 2)").
    pytest.param(
        [p256_half_order_entry(SECP256R1N // 2)],
        None,
        id="p256_s_half_order",
    ),
    pytest.param(
        # The complement `SECP256R1N - SECP256R1N // 2` is the half order
        # plus one; P256VERIFY accepts it, so only the low-`s` bound
        # rejects it.
        [p256_half_order_entry(SECP256R1N - SECP256R1N // 2)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_s_half_order_plus_one",
        marks=pytest.mark.exception_test,
    ),
    # P256 signer binding (§Transaction Signatures: "For `P256`, the
    # signer address must be `keccak256(qx || qy)[12:]`."). The
    # signature verifies with P256VERIFY, so only the binding rejects it.
    pytest.param(
        lambda sender: [p256_valid_signature(signer=Bytes(sender))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_valid_signature_explicit_foreign_signer",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The empty signer resolves to the sender (§Transaction
        # Signatures: "If absent, `tx.sender` is used").
        [p256_valid_signature()],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_valid_signature_empty_signer",
        marks=pytest.mark.exception_test,
    ),
    # P256 signer width (§Constraints: "assert len(sig.signer) == 0 or
    # len(sig.signer) == 20"). Each signer is the matching signer with a
    # byte removed or appended, and the signature verifies, so only the
    # width rejects the entry.
    pytest.param(
        [p256_valid_signature(signer=Bytes(bytes(P256_SIGNER)[:19]))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_19_bytes",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A client that reads the first 20 bytes sees the matching
        # signer.
        [p256_valid_signature(signer=Bytes(bytes(P256_SIGNER) + b"\x00"))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_21_bytes",
        marks=pytest.mark.exception_test,
    ),
]
"""
Signature entries on a boundary of a validation rule, each appended
after the canonical entry the sender's default code consumes, with the
exception the transaction must be rejected with, or `None` where the
entry sits exactly on the accepted side of the boundary.
"""

Entries = Union[List[FrameSignature], Callable[[EOA], List[FrameSignature]]]
"""Signature entries, or a callable building them from the sender."""


def bound_case_transaction(
    pre: Alloc, entries: Entries, error: Optional[TransactionException]
) -> Transaction:
    """
    Return a minimal frame transaction carrying the canonical sender
    entry followed by `entries`.
    """
    sender = pre.fund_eoa()
    case_entries = entries(sender) if callable(entries) else entries
    return Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[
            canonical_entry(sender),
            *case_entries,
        ],
        error=error,
    )


@pytest.mark.parametrize("entries,error", SIGNATURE_BOUND_CASES)
def test_signature_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    entries: Entries,
    error: Optional[TransactionException],
) -> None:
    """
    Append a signature entry on a validation boundary to a minimal frame
    transaction and check the transaction is accepted on the boundary's
    valid side and rejected one step past it.

    EIP-8141 §Signature Validation: "if v > 1 or not (0 < r <
    SECP256K1N) or not (0 < s <= SECP256K1N // 2): return False" for
    secp256k1, and "if not (0 < r < SECP256R1N) or not (0 < s <=
    SECP256R1N // 2): return False" followed by "if resolved_signer !=
    keccak256(qx + qy)[12:]: return False" for P256.
    """
    tx = bound_case_transaction(pre, entries, error)
    assert tx.sender is not None

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={tx.sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("entries,error", SIGNATURE_BOUND_CASES)
def test_signature_bounds_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    entries: Entries,
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same signature boundaries as `test_signature_bounds` on
    the transaction itself rather than on a block containing it.
    """
    transaction_test(pre=pre, tx=bound_case_transaction(pre, entries, error))


def entry_signed_for_next_nonce(pre: Alloc) -> Transaction:
    """
    Return a frame transaction whose only entry is the sender's
    canonical entry, signed over the signature hash of the same
    transaction with the next nonce.

    The canonical hash elides the entry's raw bytes and commits to
    their length only, so the two transactions differ in their nonce
    alone, and the signature recovers the sender only against the other
    transaction's hash.
    """
    sender = pre.fund_eoa()

    def with_entry(signature: bytes, nonce: int) -> Transaction:
        return Transaction(
            sender=sender,
            nonce=nonce,
            frames=[verify_frame()],
            signatures=[canonical_entry(sender, signature=Bytes(signature))],
            error=TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        )

    placeholder = bytes(SECP256K1_SIGNATURE_LENGTH)
    next_hash = with_entry(placeholder, 1).rlp_signing_bytes().keccak256()
    assert sender.key is not None
    entry = FrameSignature(scheme=Spec.SCHEME_SECP256K1)
    entry.signed_over(bytes(next_hash), sender.key)
    tx = with_entry(bytes(entry.signature), 0)
    assert tx.rlp_signing_bytes().keccak256() != next_hash
    return tx


@pytest.mark.exception_test
def test_canonical_entry_signed_for_other_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a transaction whose canonical sender entry carries a valid
    signature by the sender's key over another transaction's signature
    hash: the same transaction with the next nonce.

    EIP-8141 §Transaction Signatures: "if `len(msg) == 0`, the signature
    is signed over `compute_sig_hash(tx)`", and §Signature Validation:
    "if len(sig.msg) == 0: msg = sig_hash" followed by "return
    resolved_signer == ecrecover(msg, v, r, s)". Recovering against this
    transaction's hash does not return the sender, so the entry is
    invalid and so is the transaction.
    """
    tx = entry_signed_for_next_nonce(pre)
    assert tx.sender is not None

    state_test(pre=pre, tx=tx, post={tx.sender: Account(nonce=0)})


@pytest.mark.exception_test
def test_canonical_entry_signed_for_other_transaction_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Assert the same rejection as
    `test_canonical_entry_signed_for_other_transaction` on the
    transaction itself.
    """
    transaction_test(pre=pre, tx=entry_signed_for_next_nonce(pre))
