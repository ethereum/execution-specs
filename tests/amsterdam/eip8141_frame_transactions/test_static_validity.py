"""
Static validity tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each case starts from a minimal valid frame transaction — a single
`VERIFY` frame approving execution and payment against the sender's
default code — and applies one variation that violates a static
validity rule, or sits exactly on its boundary.

Every rule in this module is decidable from the transaction alone, so
each case fills in two formats. The state test verifies the expected
verdict against the reference implementation at fill time and pins the
absence of side effects. The transaction test pins the verdict itself:
the blockchain fixtures derived from the state test cannot — a block
carrying a wrongly-accepted transaction is invalid for a second reason,
its header committing to the rejection, so it is discarded whether or
not the implementation enforces the rule — and a transaction fixture
is recorded without a reference-implementation check, so sharing the
state test's cases is what keeps its expectations honest.

Rules that also need block context or pre-state are in
`test_admission_validity.py`.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    Frame,
    FrameSignature,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionTestFiller,
    keccak256,
)

from .helpers import (
    default_frame,
    expiry_frame,
    sender_frame,
    verify_frame,
)
from .signature_helpers import (
    DIGEST,
    P256_SIGNATURE,
    SECP256K1N,
    SECP256R1N,
    high_s_complement,
    p256_entry,
    resized_signature,
    signed_digest_entry,
    with_tampered_components,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")


def blob_hash(version: int, index: int = 0) -> Hash:
    """Return a versioned hash with the given version byte."""
    return Hash(bytes([version]) + index.to_bytes(31, "big"))


TX_FIELD_CASES = [
    pytest.param(
        # The nonce must leave room for the post-execution
        # increment, so 2**64 - 1 is already invalid.
        dict(nonce=2**64 - 1),
        TransactionException.NONCE_IS_MAX,
        id="nonce_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(max_fee_per_gas=10, max_priority_fee_per_gas=11),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
        id="priority_fee_above_max_fee",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(max_fee_per_gas=10, max_priority_fee_per_gas=10),
        None,
        id="priority_fee_equals_max_fee",
    ),
    pytest.param(
        dict(max_fee_per_gas=2**256),
        TransactionException.GASPRICE_OVERFLOW,
        id="max_fee_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(max_priority_fee_per_gas=2**256),
        TransactionException.PRIORITY_OVERFLOW,
        id="priority_fee_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(frames=[]),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="no_frames",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
            frames=[verify_frame()]
            + [default_frame() for _ in range(Spec.MAX_FRAMES)]
        ),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_count_above_max",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
            frames=[verify_frame()]
            + [default_frame() for _ in range(Spec.MAX_FRAMES - 1)]
        ),
        None,
        id="frame_count_at_max",
    ),
    pytest.param(
        dict(max_fee_per_blob_gas=1, blob_versioned_hashes=[]),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="blob_fee_without_blobs",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
            max_fee_per_blob_gas=1,
            blob_versioned_hashes=[blob_hash(version=2)],
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
        id="invalid_blob_hash_version",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
            max_fee_per_blob_gas=1,
            blob_versioned_hashes=lambda fork: [
                blob_hash(version=1, index=i)
                for i in range(fork.max_blobs_per_tx() + 1)
            ],
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
        id="blob_count_above_max",
        marks=pytest.mark.exception_test,
    ),
]
"""
Field-level variations of a minimal frame transaction, each with the
exception it must be rejected with, or `None` where the variation
sits exactly on the boundary of the rule and stays valid.
"""


@pytest.mark.parametrize("tx_overrides,error", TX_FIELD_CASES)
def test_invalid_tx_fields(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_overrides: Dict[str, Any],
    error: Optional[TransactionException],
) -> None:
    """
    Vary one transaction-level field of a minimal frame transaction and
    check that the transaction is rejected, or accepted at the exact
    boundary of the violated rule.

    Override values that depend on the fork are expressed as callables
    taking the fork, since the parametrize table is built before the
    fork is known.
    """
    sender = pre.fund_eoa()
    tx_kwargs: Dict[str, Any] = dict(
        sender=sender,
        frames=[verify_frame()],
        error=error,
    )
    tx_kwargs.update(
        {
            key: value(fork) if callable(value) else value
            for key, value in tx_overrides.items()
        }
    )
    tx = Transaction(**tx_kwargs)

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("tx_overrides,error", TX_FIELD_CASES)
def test_invalid_tx_fields_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_overrides: Dict[str, Any],
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same field-level rules as `test_invalid_tx_fields` on
    the transaction itself rather than on a block containing it; see
    the module docstring for why every static case fills both formats.
    """
    tx_kwargs: Dict[str, Any] = dict(
        sender=pre.fund_eoa(),
        frames=[verify_frame()],
        error=error,
    )
    tx_kwargs.update(
        {
            key: value(fork) if callable(value) else value
            for key, value in tx_overrides.items()
        }
    )

    transaction_test(pre=pre, tx=Transaction(**tx_kwargs))


FOREIGN_TARGET = Address(0x1234)
"""An address that is never the transaction sender."""


FRAME_CASES = [
    pytest.param(
        [verify_frame(), default_frame(value=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="default_frame_with_value",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(value=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="verify_frame_with_value",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # An empty target resolves to the sender, so the value is
        # transferred to itself.
        [verify_frame(), sender_frame(value=1)],
        None,
        id="sender_frame_with_value",
    ),
    pytest.param(
        [
            verify_frame(flags=Spec.APPROVE_EXECUTION, target=FOREIGN_TARGET),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="approve_execution_frame_with_foreign_target",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only targeting the sender explicitly differs from the
        # minimal transaction's empty target.
        lambda _pre, sender: [verify_frame(target=sender)],
        None,
        id="approve_execution_frame_with_explicit_sender_target",
    ),
    pytest.param(
        [
            verify_frame(),
            verify_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_flag_on_verify_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_flag_on_last_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            verify_frame(flags=Spec.APPROVE_NONE),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_batch_followed_by_verify_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Identical to `atomic_flag_on_last_frame` except for the
        # trailing batch terminator, which makes the batch valid.
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(),
        ],
        None,
        id="atomic_batch_of_default_frames",
    ),
    pytest.param(
        # Each frame's gas limit fits into 64 bits, but the total
        # frame gas must as well.
        [
            verify_frame(),
            default_frame(gas_limit=2**64 - 1),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_gas_sum_overflows",
        marks=pytest.mark.exception_test,
    ),
    # Decode-time rejections: field values outside their type's
    # domain never construct, so the transaction never decodes.
    pytest.param(
        [verify_frame(), default_frame(mode=3)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_frame_mode",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), default_frame(mode=255)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_frame_mode_high",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), default_frame(flags=0x08)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flag",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), default_frame(flags=0xFF)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flag_high",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), default_frame(gas_limit=2**64)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_gas_above_64_bits",
        marks=pytest.mark.exception_test,
    ),
]
"""
Frame-list variations of a minimal frame transaction, each with the
exception it must be rejected with, or `None` where the variation is
the nearest-valid counterpart of a rejected case.
"""


@pytest.mark.parametrize("frames,error", FRAME_CASES)
def test_frame_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: Optional[TransactionException],
) -> None:
    """
    Vary the frame list of a minimal frame transaction and check that
    per-frame static constraints reject the transaction, or accept the
    nearest-valid variant.

    Frame lists that depend on the pre-state or the sender are
    expressed as callables taking both, since the parametrize table is
    built before either is known.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=frames(pre, sender) if callable(frames) else frames,
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("frames,error", FRAME_CASES)
def test_frame_constraints_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same per-frame rules as `test_frame_constraints` on the
    transaction itself rather than on a block containing it; see the
    module docstring for why every static case fills both formats.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=frames(pre, sender) if callable(frames) else frames,
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


EXPIRY_VERIFIER_CASES = [
    pytest.param(
        [verify_frame(), expiry_frame(data=b"")],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_empty",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), expiry_frame(data=b"\xff" * 7)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), expiry_frame(data=b"\xff" * 9)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), expiry_frame(flags=Spec.APPROVE_PAYMENT)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_flags",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), expiry_frame(value=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_value",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Each frame on its own is well-formed; only their
        # multiplicity violates the rule.
        [verify_frame(), expiry_frame(), expiry_frame()],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="multiple_expiry_frames",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The expiry shape rules apply only to `VERIFY` frames, so
        # a `DEFAULT` frame targeting the predeploy may carry data
        # of any length. Its execution reverts, but a failing
        # non-`VERIFY` frame does not invalidate the transaction.
        [
            verify_frame(),
            default_frame(target=Spec.EXPIRY_VERIFIER, data=b"\xff" * 7),
        ],
        None,
        id="default_frame_targeting_expiry_verifier",
    ),
    pytest.param(
        # The expiry shape rules key on the predeploy's address, so
        # a `VERIFY` frame elsewhere may carry data of any length.
        # The target must hold code that succeeds, since the
        # default verify code fails frames with no approval scope.
        lambda pre, _sender: [
            verify_frame(),
            verify_frame(
                flags=Spec.APPROVE_NONE,
                target=pre.deploy_contract(code=Op.STOP),
                data=b"\xff" * 7,
            ),
        ],
        None,
        id="verify_frame_with_expiry_data_to_other_target",
    ),
]
"""
Shape variations of an expiry verifier frame — a `VERIFY` frame
targeting the expiry verifier predeploy — each with the exception it
must be rejected with, or `None` where the variation is the
nearest-valid counterpart of a rejected case.
"""


@pytest.mark.parametrize("frames,error", EXPIRY_VERIFIER_CASES)
def test_expiry_verifier_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: Optional[TransactionException],
) -> None:
    """
    Vary the shape of an expiry verifier frame — a `VERIFY` frame
    targeting the expiry verifier predeploy — and check that its
    static constraints reject the transaction, or accept the
    nearest-valid variant.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=frames(pre, sender) if callable(frames) else frames,
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("frames,error", EXPIRY_VERIFIER_CASES)
def test_expiry_verifier_constraints_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same expiry verifier frame rules as
    `test_expiry_verifier_constraints` on the transaction itself rather
    than on a block containing it; see the module docstring for why
    every static case fills both formats.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=frames(pre, sender) if callable(frames) else frames,
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


SIGNATURE_CASES = [
    # secp256k1 entries, built from a valid signature over an
    # explicit digest and tampered in a single component.
    pytest.param(
        lambda _pre, sender: [signed_digest_entry(sender.key)],
        None,
        id="secp256k1_digest_entry",
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_signature(signed_digest_entry(sender.key), 64)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_signature_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_signature(signed_digest_entry(sender.key), 66)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_signature_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_signature(signed_digest_entry(sender.key), 0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_signature_empty",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_entry(sender.key), v=2)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_2",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The legacy transaction v encoding is not valid here.
        lambda _pre, sender: [
            with_tampered_components(signed_digest_entry(sender.key), v=27)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_27",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_entry(sender.key), r=0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(
                signed_digest_entry(sender.key), r=SECP256K1N
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_at_curve_order",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_entry(sender.key), s=0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_s_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            high_s_complement(signed_digest_entry(sender.key))
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_high_s",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A valid signature whose explicit signer is a different
        # address than the signature recovers to.
        lambda _pre, sender: [
            signed_digest_entry(sender.key, signer=Bytes(FOREIGN_TARGET))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="secp256k1_signer_mismatch",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # An empty signer resolves to the sender, but the entry is
        # signed with an unrelated key.
        lambda _pre, _sender: [signed_digest_entry(Hash(1))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="secp256k1_wrong_key",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_entry(sender.key, signer=Bytes(b"\x01" * 19))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="signer_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_entry(sender.key, signer=Bytes(b"\x01" * 21))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="signer_too_long",
        marks=pytest.mark.exception_test,
    ),
    # Message shape rules, checked before any scheme dispatch, so
    # an `ARBITRARY` entry keeps each case to a single violation.
    pytest.param(
        [FrameSignature(scheme=Spec.SCHEME_ARBITRARY, msg=Bytes(b"\x01"))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_single_byte",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, msg=Bytes(b"\x01" * 31)
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, msg=Bytes(b"\x01" * 33)
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The all-zero digest is reserved as the EVM-visible
        # representation of the canonical-hash case.
        [
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, msg=Bytes(b"\x00" * 32)
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_all_zeros",
        marks=pytest.mark.exception_test,
    ),
    # ARBITRARY entries.
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY,
                signature=Bytes(b"\xab" * 5),
            )
        ],
        None,
        id="arbitrary_entry",
    ),
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY,
                signer=Bytes(FOREIGN_TARGET),
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="arbitrary_with_signer",
        marks=pytest.mark.exception_test,
    ),
    # P256 entries.
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_P256,
                msg=Bytes(DIGEST),
                signer=Bytes(keccak256(P256_SIGNATURE[64:])[12:]),
                signature=Bytes(P256_SIGNATURE),
            )
        ],
        None,
        id="p256_valid_entry",
    ),
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_P256,
                msg=Bytes(DIGEST),
                signer=Bytes(keccak256(P256_SIGNATURE[64:])[12:]),
                signature=Bytes(P256_SIGNATURE[:127]),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_signature_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            FrameSignature(
                scheme=Spec.SCHEME_P256,
                msg=Bytes(DIGEST),
                signer=Bytes(keccak256(P256_SIGNATURE[64:])[12:]),
                signature=Bytes(P256_SIGNATURE + b"\x00"),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_signature_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [p256_entry(r=0, s=1)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [p256_entry(r=SECP256R1N, s=1)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_at_curve_order",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [p256_entry(r=1, s=0)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_s_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [p256_entry(r=1, s=SECP256R1N // 2 + 1)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_high_s",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The empty signer resolves to the sender, which never
        # matches the hash of the entry's public key words.
        [p256_entry(r=1, s=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_mismatch",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The signer matches the public key words, but (0, 0) is
        # not a point on the P-256 curve.
        [
            p256_entry(
                r=1,
                s=1,
                signer=Bytes(keccak256(b"\x00" * 64)[12:]),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_not_on_curve",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A well-formed signature over a different digest than the
        # entry's msg fails cryptographic verification.
        [
            FrameSignature(
                scheme=Spec.SCHEME_P256,
                msg=Bytes(b"\x02" * 32),
                signer=Bytes(keccak256(P256_SIGNATURE[64:])[12:]),
                signature=Bytes(P256_SIGNATURE),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_signature_over_different_digest",
        marks=pytest.mark.exception_test,
    ),
    # Decode-time rejections: a signature scheme outside the
    # defined set never constructs, so the transaction never
    # decodes.
    pytest.param(
        [FrameSignature(scheme=3)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_signature_scheme",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [FrameSignature(scheme=255)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_signature_scheme_high",
        marks=pytest.mark.exception_test,
    ),
]
"""
Variations of a single signature entry, appended after the canonical
entry consumed by the sender's default code, each with the exception
it must be rejected with, or `None` where the variation is the
nearest-valid counterpart of a rejected case.
"""


@pytest.mark.parametrize("entries,error", SIGNATURE_CASES)
def test_signature_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    entries: Union[
        List[FrameSignature],
        Callable[[Alloc, EOA], List[FrameSignature]],
    ],
    error: Optional[TransactionException],
) -> None:
    """
    Vary a single signature entry of a minimal frame transaction and
    check that the protocol's structural and cryptographic entry
    validation rejects the transaction, or accepts the nearest-valid
    variant.

    The varied entry is appended after the canonical entry consumed by
    the sender's default code, so every case differs from a valid
    transaction only in the appended entry.
    """
    sender = pre.fund_eoa()
    case_entries = entries(pre, sender) if callable(entries) else entries
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            *case_entries,
        ],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("entries,error", SIGNATURE_CASES)
def test_signature_constraints_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    entries: Union[
        List[FrameSignature],
        Callable[[Alloc, EOA], List[FrameSignature]],
    ],
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same signature entry rules as
    `test_signature_constraints` on the transaction itself rather than
    on a block containing it; see the module docstring for why every
    static case fills both formats.
    """
    sender = pre.fund_eoa()
    case_entries = entries(pre, sender) if callable(entries) else entries
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            *case_entries,
        ],
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


# The gas boundary tests use a contract sender: contract senders carry
# no signature entries, so the transaction's intrinsic cost reduces to
# the base and per-frame constants plus its data tokens, keeping the
# boundary arithmetic exact and content-independent.


FRAME_GAS_CAP_CASES = [
    pytest.param(0, None, id="at_cap"),
    pytest.param(
        1,
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        id="above_cap",
        marks=pytest.mark.exception_test,
    ),
]
"""
Gas in excess of the per-transaction cap, driven by a frame's gas
limit, with the exception the excess must be rejected with.
"""


@pytest.mark.parametrize("cap_excess,error", FRAME_GAS_CAP_CASES)
def test_gas_limit_cap_from_frame_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    cap_excess: int,
    error: Optional[TransactionException],
) -> None:
    """
    Size a frame's gas limit so the transaction's derived gas limit —
    intrinsic cost plus the frame gas — lands exactly on the
    per-transaction gas cap, or one above it.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    # A contract sender carries no signature entries and the frame no
    # data, so a frame count prices the intrinsic cost exactly.
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=1,
        return_cost_deducted_prior_execution=True,
    )
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(gas_limit=cap - intrinsic + cap_excess)],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if error else 2)},
    )


@pytest.mark.parametrize("cap_excess,error", FRAME_GAS_CAP_CASES)
def test_gas_limit_cap_from_frame_gas_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    cap_excess: int,
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same gas cap rule as `test_gas_limit_cap_from_frame_gas`
    on the transaction itself rather than on a block containing it; see
    the module docstring for why every static case fills both formats.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=1,
        return_cost_deducted_prior_execution=True,
    )
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(gas_limit=cap - intrinsic + cap_excess)],
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


CALLDATA_FLOOR_CAP_CASES = [
    pytest.param(0, None, id="below_cap"),
    pytest.param(
        1,
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        id="above_cap",
        marks=pytest.mark.exception_test,
    ),
]
"""
Gas in excess of the per-transaction cap, driven by the calldata
floor, with the exception the excess must be rejected with.
"""


@pytest.mark.parametrize("cap_excess,error", CALLDATA_FLOOR_CAP_CASES)
def test_gas_limit_cap_from_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    cap_excess: int,
    error: Optional[TransactionException],
) -> None:
    """
    Drive the calldata floor across the per-transaction gas cap with
    zero-byte frame data while the standard gas limit stays far below
    it, pinning that the cap applies to the larger of the two anchors.

    The cap is not a multiple of the per-byte floor cost, so the
    boundary pair is the largest data length whose floor fits under
    the cap and the first one whose floor exceeds it.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    gas_costs = fork.gas_costs()
    floor_per_byte = (
        gas_costs.TX_DATA_TOKEN_STANDARD * gas_costs.TX_DATA_TOKEN_FLOOR
    )
    # With no charged bytes the floor anchor is the always-paid base
    # costs alone; the data length is solved against it below.
    base = fork.frame_transaction_data_floor_cost_calculator()(frames=2)
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    data_length = (cap - base) // floor_per_byte + cap_excess

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(),
            default_frame(gas_limit=0, data=Bytes(b"\x00" * data_length)),
        ],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if error else 2)},
    )


@pytest.mark.parametrize("cap_excess,error", CALLDATA_FLOOR_CAP_CASES)
def test_gas_limit_cap_from_calldata_floor_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    cap_excess: int,
    error: Optional[TransactionException],
) -> None:
    """
    Assert the same gas cap rule as
    `test_gas_limit_cap_from_calldata_floor` on the transaction itself
    rather than on a block containing it; see the module docstring for
    why every static case fills both formats.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    gas_costs = fork.gas_costs()
    floor_per_byte = (
        gas_costs.TX_DATA_TOKEN_STANDARD * gas_costs.TX_DATA_TOKEN_FLOOR
    )
    # With no charged bytes the floor anchor is the always-paid base
    # costs alone; the data length is solved against it below.
    base = fork.frame_transaction_data_floor_cost_calculator()(frames=2)
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    data_length = (cap - base) // floor_per_byte + cap_excess

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(),
            default_frame(gas_limit=0, data=Bytes(b"\x00" * data_length)),
        ],
        error=error,
    )

    transaction_test(pre=pre, tx=tx)
