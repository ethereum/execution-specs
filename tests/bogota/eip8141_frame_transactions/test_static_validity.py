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

Two bound tests fill the transaction format only, since no block can
isolate their bound: no account nonce reaches `2**64`
(`test_nonce_at_bound_transaction`), and a frame gas sum near `2**64`
holds a state budget no block fits
(`test_frame_gas_sum_bound_transaction`). The valid side of that sum in
a block is `test_admission_validity.py::test_frame_gas_sum_bound_in_block`.

Rules that also need block context or pre-state are in
`test_admission_validity.py`.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import pytest
from execution_testing import (
    EOA,
    SECP256K1_SIGNATURE_LENGTH,
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
    EXPIRY_VERIFIER_LENGTH_REJECTING_PATH,
    FrameCase,
    FrameTransaction,
    Outcome,
    approving_contract_sender,
    default_frame,
    expiry_frame,
    frame_gas_sum_frames,
    sender_frame,
    sponsored_signatures,
    verify_frame,
)
from .signature_helpers import (
    DIGEST,
    P256_S,
    P256_SIGNATURE,
    P256_SIGNER,
    SECP256K1N,
    SECP256R1N,
    canonical_entry,
    high_s_complement,
    p256_entry,
    p256_public_key,
    p256_sign,
    resized_signature,
    signed_digest_entry,
    valid_p256_entry,
    with_tampered_components,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


def blob_hash(version: int, index: int = 0) -> Hash:
    """Return a versioned hash with the given version byte."""
    return Hash(bytes([version]) + index.to_bytes(31, "big"))


TX_FIELD_CASES = [
    pytest.param(
        # The nonce must leave room for the post-execution
        # increment, so 2**64 - 1 is already invalid. The state test
        # gives the sender that nonce, so the transaction breaks no
        # other rule.
        dict(nonce=2**64 - 1),
        TransactionException.NONCE_IS_MAX,
        id="nonce_overflow",
        marks=[pytest.mark.exception_test, pytest.mark.pre_alloc_mutable],
    ),
    pytest.param(
        dict(max_fee=2**256),
        TransactionException.GASPRICE_OVERFLOW,
        id="max_fee_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only the `max_fee` budget caps the tip, so no tip per gas is
        # too high for it.
        dict(max_priority_fee_per_gas=2**256 - 1),
        None,
        id="priority_fee_at_max",
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
        dict(blob_versioned_hashes=[blob_hash(version=2)]),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
        id="invalid_blob_hash_version",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
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
    # An overridden nonce is the sender's nonce too, so a case about
    # the nonce's bound is not also a nonce mismatch.
    nonce = tx_overrides.get("nonce", 0)
    sender = pre.fund_eoa(
        **({"nonce": nonce} if "nonce" in tx_overrides else {})
    )
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
        post={sender: Account(nonce=nonce if error else nonce + 1)},
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


NONCE_BOUND = 2**64
"""The bound §Constraints writes for a frame transaction's nonce."""


@pytest.mark.exception_test
def test_nonce_at_bound_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose nonce is `2**64`, the value
    §Constraints bounds the nonce by and the first that does not fit in
    64 bits.

    It is not the first nonce rejected: the nonce must also leave room
    for the sender's increment, so `2**64 - 1` is already invalid. That
    boundary's pair is `test_admission_validity.py::test_nonce_at_maximum`
    (`2**64 - 2`, accepted) and the `nonce_overflow` case of
    `TX_FIELD_CASES` (`2**64 - 1`, rejected).

    No account nonce reaches `2**64`, so in a block the transaction would
    also mismatch its sender's nonce, and the EIP does not order the two
    checks. Only the transaction itself isolates the bound.

    EIP-8141 §Constraints: "assert tx.nonce < 2**64".
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        nonce=NONCE_BOUND,
        frames=[verify_frame()],
        # The EIP does not say whether the nonce field is decoded as a
        # 64-bit integer. A client that does fails to decode this one
        # (`NONCE_OVERFLOW`); one that decodes a wider integer, as the
        # reference implementation does, rejects it at the
        # room-for-increment check (`NONCE_IS_MAX`).
        error=[
            TransactionException.NONCE_IS_MAX,
            TransactionException.NONCE_OVERFLOW,
        ],
    )

    transaction_test(pre=pre, tx=tx)


ZERO_ADDRESS = Address(0)
"""A sender the static rules accept: they only check its length."""


# Placing code at a fixed address mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
def test_zero_address_sender(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept a frame transaction sent from the zero address, whose code
    approves execution and payment.
    """
    pre[ZERO_ADDRESS] = Account(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    tx = Transaction(sender=ZERO_ADDRESS, frames=[verify_frame()])

    state_test(pre=pre, tx=tx, post={ZERO_ADDRESS: Account(nonce=1)})


def test_zero_address_sender_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept the zero-address sender of `test_zero_address_sender` on the
    transaction itself.
    """
    tx = Transaction(sender=ZERO_ADDRESS, frames=[verify_frame()])

    transaction_test(pre=pre, tx=tx)


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
        # Approval scope is disallowed on every frame of a batch. This is
        # the flagged member; `atomic_batch_of_default_frames` above is the
        # same shape without the scope, and is valid.
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG | Spec.APPROVE_PAYMENT),
            default_frame(),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="approval_scope_on_flagged_batch_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The terminating frame carries no flag of its own but still
        # belongs to the batch, so the same rule applies to it. Without
        # this case an implementation that only checks flagged frames
        # passes, and the approval context is no longer constant across
        # the batch.
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(flags=Spec.APPROVE_PAYMENT),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="approval_scope_on_batch_terminating_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A frame after the batch has ended is unaffected: the terminator
        # closed the batch, so this frame is outside it. Pins the rule's
        # upper boundary, so an implementation cannot satisfy the two cases
        # above by rejecting approval scope on any frame following a batch.
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(),
            default_frame(flags=Spec.APPROVE_PAYMENT),
        ],
        None,
        id="approval_scope_after_batch_terminator",
    ),
    # §Constraints: "if frame.flags & ATOMIC_BATCH_FLAG or (i > 0 and
    # tx.frames[i - 1].flags & ATOMIC_BATCH_FLAG): assert frame.flags &
    # APPROVE_SCOPE_MASK == 0", where `APPROVE_SCOPE_MASK` covers the
    # execution bit as well as the payment bit of the three cases above.
    pytest.param(
        # The execution bit alone, on a flagged frame whose empty target
        # keeps the execution scope's own target rule satisfied.
        [
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG | Spec.APPROVE_EXECUTION
            ),
            default_frame(),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="execution_scope_on_flagged_batch_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG
                | Spec.APPROVE_EXECUTION_AND_PAYMENT
            ),
            default_frame(),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="both_scopes_on_flagged_batch_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(flags=Spec.APPROVE_EXECUTION),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="execution_scope_on_batch_terminating_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(flags=Spec.APPROVE_EXECUTION_AND_PAYMENT),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="both_scopes_on_batch_terminating_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            verify_frame(),
            sender_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            sender_frame(flags=Spec.APPROVE_PAYMENT),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="payment_scope_on_sender_batch_terminating_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The nearest-valid counterpart of the case above.
        [
            verify_frame(),
            sender_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            sender_frame(),
        ],
        None,
        id="sender_batch_without_scope",
    ),
    pytest.param(
        # The execution bit is allowed on the frame after the batch's
        # terminator, which no longer belongs to the batch.
        [
            verify_frame(),
            default_frame(flags=Spec.ATOMIC_BATCH_FLAG),
            default_frame(),
            default_frame(flags=Spec.APPROVE_EXECUTION),
        ],
        None,
        id="execution_scope_after_batch_terminator",
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
    pytest.param(
        # The total sums both dimensions, so a state budget drives
        # the same overflow.
        [
            verify_frame(),
            default_frame(state_gas_limit=2**64 - 1),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_state_gas_sum_overflows",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Each dimension's budget fits into 64 bits on its own; only
        # their cross-dimension sum overflows.
        [
            verify_frame(),
            default_frame(gas_limit=2**63, state_gas_limit=2**63),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_gas_cross_dimension_sum_overflows",
        marks=pytest.mark.exception_test,
    ),
    # Decode-time rejections: field values outside their type's
    # domain never construct, so the transaction never decodes.
    pytest.param(
        [verify_frame(), Frame(mode=3)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_frame_mode",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [verify_frame(), Frame(mode=255)],
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
    pytest.param(
        [verify_frame(), default_frame(state_gas_limit=2**64)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_state_gas_above_64_bits",
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


FRAME_GAS_SUM_CASES = [
    pytest.param(0, None, id="sum_2_pow_64_minus_one"),
    pytest.param(
        1,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="sum_2_pow_64",
        marks=pytest.mark.exception_test,
    ),
]
"""
Excess of the frame gas sum over `2**64 - 1`, with the exception the
transaction must be rejected with, or `None` if it is valid.
"""


@pytest.mark.parametrize("excess,error", FRAME_GAS_SUM_CASES)
def test_frame_gas_sum_bound_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    excess: int,
    error: Optional[TransactionException],
) -> None:
    """
    Sum the frames' execution and state budgets to exactly `2**64 - 1`,
    which is valid, or to `2**64`, which is not.

    EIP-8141 §Constraints: "total_frame_gas += frame.limits.execution +
    frame.limits.state" and "assert total_frame_gas < 2**64".
    """
    tx = Transaction(
        sender=approving_contract_sender(pre),
        nonce=1,
        frames=frame_gas_sum_frames(excess),
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
        # The expiry verifier creates no state, so its frame must
        # declare no state gas budget.
        [verify_frame(), expiry_frame(state_gas_limit=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_state_gas",
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


# Signature vectors on the numeric boundaries of §Signature Validation.
# A secp256k1 signature with `r = Gx` (the generator's x-coordinate)
# over `DIGEST` recovers a different public key for every `s` and
# recovery id, so a chosen `s` determines its signer. Each signer below
# was computed with plain ECDSA public key recovery,
# `Q = r^-1 * (s * R - z * G)`, where `R` is the curve point with
# x-coordinate `r` and the parity given by `v`.

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
    # secp256k1 recovery id (§Signature Validation: "v is the recovery
    # id (0 or 1)"). Each entry's explicit signer is its key's own
    # address, so only the `v` byte can reject it.
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
        lambda _pre, sender: [
            with_tampered_components(signed_digest_entry(sender.key), v=2)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_2",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The legacy transaction `v` encoding, `27` plus the true
        # recovery id: a client that normalizes it recovers the
        # explicit signer, so only the recovery id rule rejects it.
        [
            with_tampered_components(
                recovery_id_entry(KEY_RECOVERY_ID_0, 0), v=27
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_27",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            with_tampered_components(
                recovery_id_entry(KEY_RECOVERY_ID_1, 1), v=28
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_28",
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
        # `r` above the order is still the x-coordinate of a curve
        # point, so recovery without the range check (§Signature
        # Validation: "not (0 < r < SECP256K1N)") returns this signer.
        [
            secp256k1_vector(
                0, SECP256K1_R_ABOVE_ORDER, 5, SECP256K1_R_ABOVE_ORDER_SIGNER
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_above_order_on_curve",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Plain recovery accepts `s = 0` and returns this signer, so only
        # the lower bound of `s` rejects the entry.
        [secp256k1_vector(0, SECP256K1_GX, 0, SECP256K1_S_ZERO_SIGNER)],
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
    # The upper bound of `s` itself (§Signature Validation: "not (0 < s
    # <= SECP256K1N // 2)"), accepted for both recovery ids.
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
    # Each entry below keeps the valid public key words and the signer
    # they hash to, so only the rule on the tampered component is broken
    # and a client checking the signer first rejects it the same way.
    pytest.param(
        [valid_p256_entry(r=0)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [valid_p256_entry(r=SECP256R1N)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_at_curve_order",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [valid_p256_entry(s=0)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_s_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The high-`s` complement is algebraically valid but rejected
        # by the canonical-encoding rule, as for secp256k1.
        [valid_p256_entry(s=SECP256R1N - P256_S)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_high_s",
        marks=pytest.mark.exception_test,
    ),
    # The upper bound of `s` itself (§Signature Validation: "not (0 < s
    # <= SECP256R1N // 2)").
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
        # The empty signer resolves to the sender (§Transaction
        # Signatures: "If absent, `tx.sender` is used").
        [p256_valid_signature()],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_mismatch",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [p256_valid_signature(signer=Bytes(sender))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_valid_signature_explicit_foreign_signer",
        marks=pytest.mark.exception_test,
    ),
    # P256 signer width (§Constraints: "assert len(sig.signer) == 0 or
    # len(sig.signer) == 20"), on a signature that verifies.
    pytest.param(
        # The matching signer with its last byte removed. No 19-byte
        # signer equals the 20-byte hash, so a client without the width
        # rule rejects the entry for the mismatch, with the same error:
        # the case pins the error, not the width rule.
        [p256_valid_signature(signer=Bytes(bytes(P256_SIGNER)[:19]))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_19_bytes",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The matching signer with a byte appended. A client that reads
        # the first 20 bytes sees the matching signer, so only the width
        # rule rejects the entry.
        [p256_valid_signature(signer=Bytes(bytes(P256_SIGNER) + b"\x00"))],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_signer_21_bytes",
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

    The boundary cases follow EIP-8141 §Signature Validation: "if v > 1
    or not (0 < r < SECP256K1N) or not (0 < s <= SECP256K1N // 2):
    return False" for secp256k1, and "if not (0 < r < SECP256R1N) or
    not (0 < s <= SECP256R1N // 2): return False" followed by "if
    resolved_signer != keccak256(qx + qy)[12:]: return False" for P256.
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


def test_gas_limit_cap_exempts_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Declare a state gas budget as large as the per-transaction gas cap
    on a transaction whose execution dimension sits exactly at the cap.

    The cap of EIP-7825 binds the execution dimension alone, so the
    state budget does not count toward it and the transaction stays
    valid.
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
        frames=[verify_frame(gas_limit=cap - intrinsic, state_gas_limit=cap)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2)},
    )


def test_gas_limit_cap_exempts_state_gas_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Assert the same state gas exemption as
    `test_gas_limit_cap_exempts_state_gas` on the transaction itself
    rather than on a block containing it; see the module docstring for
    why every static case fills both formats.
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
        frames=[verify_frame(gas_limit=cap - intrinsic, state_gas_limit=cap)],
    )

    transaction_test(pre=pre, tx=tx)


def calldata_floor_cap_frames(
    fork: Fork, target: Address, cap_excess: int
) -> List[FrameCase]:
    """
    Return frames whose calldata floor equals the per-transaction gas
    cap, plus `cap_excess` zero bytes of data at the floor price each.

    The floor is the always-paid base costs plus a fixed price per data
    byte, and the cap is not a multiple of that price. The per-frame
    cost is odd, so a suitable frame count makes the gap between the cap
    and the base costs a whole number of bytes. After the `VERIFY`
    frame, every frame calls `target` with just enough gas for its cold
    entry, and the last one carries the data.
    """
    floor_calculator = fork.frame_transaction_data_floor_cost_calculator()
    # The floor price of one data byte, whatever its value.
    floor_per_byte = floor_calculator(
        frames=[Frame(data=Bytes(b"\x00"))]
    ) - floor_calculator(frames=[Frame()])
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    frame_count = next(
        count
        for count in range(2, Spec.MAX_FRAMES + 1)
        if (cap - floor_calculator(frames=count)) % floor_per_byte == 0
    )
    data_length = (
        cap - floor_calculator(frames=frame_count)
    ) // floor_per_byte + cap_excess

    entry_gas = fork.frame_entry_gas_calculator()()
    frames = [verify_frame(state_gas_limit=0)] + [
        default_frame(target=target, gas_limit=entry_gas, state_gas_limit=0)
        for _ in range(frame_count - 1)
    ]
    frames[-1].data = Bytes(b"\x00" * data_length)
    # The premise: the floor sits exactly `cap_excess` byte prices from
    # the cap.
    assert floor_calculator(frames=frames) == cap + cap_excess * floor_per_byte

    # The intrinsic cost plus the frame execution budgets stays below
    # the cap, so only the floor can exceed it.
    standard = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, return_cost_deducted_prior_execution=True
    ) + sum(int(frame.gas_limit) for frame in frames)
    assert standard < cap
    return frames


CALLDATA_FLOOR_CAP_CASES = [
    pytest.param(-1, None, id="below_cap"),
    pytest.param(0, None, id="at_cap"),
    pytest.param(
        1,
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        id="above_cap",
        marks=pytest.mark.exception_test,
    ),
]
"""
Zero bytes of data in excess of a calldata floor equal to the
per-transaction cap, with the exception the excess must be rejected
with.
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
    Drive the calldata floor to one data byte below the per-transaction
    gas cap, exactly onto it, and one byte past it with zero-byte frame
    data, while the intrinsic cost plus the frame execution budgets
    stays far below the cap, pinning that the cap applies to the larger
    of the two anchors and admits a floor equal to it.

    EIP-8141 §Constraints: "assert max(frame_tx_intrinsic_gas +
    total_frame_execution_gas, calldata_floor_gas) <= TX_MAX_GAS_LIMIT".
    """
    sender = approving_contract_sender(pre)
    target = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=calldata_floor_cap_frames(fork, target, cap_excess),
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
    sender = approving_contract_sender(pre)
    target = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=calldata_floor_cap_frames(fork, target, cap_excess),
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


def sender_frames_to_expiry_verifier() -> List[FrameCase]:
    """
    Return a `VERIFY` frame approving execution and payment, then two
    `SENDER` frames calling the expiry verifier with 9 bytes of data
    and with none, both of which revert.
    """
    return [
        verify_frame(),
        *(
            sender_frame(
                target=Spec.EXPIRY_VERIFIER,
                data=data,
                code=EXPIRY_VERIFIER_LENGTH_REJECTING_PATH,
                outcome=Outcome.REVERT,
            )
            for data in (b"\xff" * (Spec.EXPIRY_DATA_LENGTH + 1), b"")
        ),
    ]


def test_sender_frame_to_expiry_verifier(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Call the expiry verifier from `SENDER` frames with calldata that is
    not 8 bytes long. The frames are not expiry verifier frames, so its
    shape rules do not apply and the transaction is valid; the contract
    itself rejects the calldata length, so both frames revert.

    EIP-8141 §Expiry Verifier Frame: "A `VERIFY` frame whose
    `frame.target` equals `EXPIRY_VERIFIER` is an **expiry verifier
    frame**." and "if len(evm.calldata) != EXPIRY_DATA_LENGTH:
    revert()".
    """
    sender = pre.fund_eoa()
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=sender_frames_to_expiry_verifier(),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_sender_frame_to_expiry_verifier_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept the transaction of `test_sender_frame_to_expiry_verifier` on
    the transaction itself.
    """
    tx = Transaction(
        sender=pre.fund_eoa(), frames=sender_frames_to_expiry_verifier()
    )

    transaction_test(pre=pre, tx=tx)


MAX_FRAME_VALUE = 2**256 - 1
"""The largest value a frame may carry."""


def sponsored_max_value_frames(payer: EOA) -> List[FrameCase]:
    """
    Return frames in which the sender approves execution, `payer`
    approves payment, and a `SENDER` frame with an empty target sends
    the largest frame value from the sender to itself.
    """
    return [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
        sender_frame(value=MAX_FRAME_VALUE),
    ]


def test_sender_frame_value_at_max(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Accept a `SENDER` frame carrying `2**256 - 1`, the largest value the
    bound allows. A separate payer covers the fees, so the sender holds
    the whole value and the transfer to itself succeeds.

    EIP-8141 §Constraints: "assert frame.value < 2**256" and "assert
    frame.mode == SENDER or frame.value == 0".
    """
    sender = pre.fund_eoa(amount=MAX_FRAME_VALUE)
    payer = pre.fund_eoa()
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=sponsored_max_value_frames(payer),
        signatures=sponsored_signatures(sender, payer),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=MAX_FRAME_VALUE),
            payer: Account(nonce=0),
        },
    )


def test_sender_frame_value_at_max_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept the transaction of `test_sender_frame_value_at_max` on the
    transaction itself.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=sponsored_max_value_frames(payer),
        signatures=sponsored_signatures(sender, payer),
    )

    transaction_test(pre=pre, tx=tx)
