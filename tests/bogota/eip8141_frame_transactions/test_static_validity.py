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
    Claim,
    Fork,
    Frame,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)
from execution_testing.test_types import TransactionDefaults

from .claim_helpers import DIGEST, signed_digest_claim
from .helpers import fee_budget
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
            frames=[Frame.verify()]
            + [Frame.default() for _ in range(Spec.MAX_FRAMES)]
        ),
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_count_above_max",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(
            frames=[Frame.verify()]
            + [Frame.default() for _ in range(Spec.MAX_FRAMES - 1)]
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
        frames=[Frame.verify()],
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
        frames=[Frame.verify()],
        error=error,
    )
    tx_kwargs.update(
        {
            key: value(fork) if callable(value) else value
            for key, value in tx_overrides.items()
        }
    )

    transaction_test(pre=pre, tx=Transaction(**tx_kwargs))


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
    tx = Transaction(sender=ZERO_ADDRESS, frames=[Frame.verify()])

    state_test(pre=pre, tx=tx, post={ZERO_ADDRESS: Account(nonce=1)})


def test_zero_address_sender_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept the zero-address sender of `test_zero_address_sender` on the
    transaction itself.
    """
    tx = Transaction(sender=ZERO_ADDRESS, frames=[Frame.verify()])

    transaction_test(pre=pre, tx=tx)


FOREIGN_TARGET = Address(0x1234)
"""An address that is never the transaction sender."""


FRAME_CASES = [
    pytest.param(
        [Frame.verify(), Frame.default(value=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="default_frame_with_value",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(value=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="verify_frame_with_value",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # An empty target resolves to the sender, so the value is
        # transferred to itself.
        [Frame.verify(), Frame.sender(value=1)],
        None,
        id="sender_frame_with_value",
    ),
    pytest.param(
        [
            Frame.verify(flags=Spec.APPROVE_EXECUTION, target=FOREIGN_TARGET),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="approve_execution_frame_with_foreign_target",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only targeting the sender explicitly differs from the
        # minimal transaction's empty target.
        lambda _pre, sender: [Frame.verify(target=sender)],
        None,
        id="approve_execution_frame_with_explicit_sender_target",
    ),
    pytest.param(
        [
            Frame.verify(),
            Frame.verify(flags=Spec.ATOMIC_BATCH_FLAG),
            Frame.default(),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_flag_on_verify_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_flag_on_last_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG),
            Frame.verify(flags=Spec.APPROVE_NONE),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="atomic_batch_followed_by_verify_frame",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Identical to `atomic_flag_on_last_frame` except for the
        # trailing batch terminator, which makes the batch valid.
        [
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG),
            Frame.default(),
        ],
        None,
        id="atomic_batch_of_default_frames",
    ),
    pytest.param(
        # Approval scope is disallowed on every frame of a batch. This is
        # the flagged member; `atomic_batch_of_default_frames` above is the
        # same shape without the scope, and is valid.
        [
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG | Spec.APPROVE_PAYMENT),
            Frame.default(),
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
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG),
            Frame.default(flags=Spec.APPROVE_PAYMENT),
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
            Frame.verify(),
            Frame.default(flags=Spec.ATOMIC_BATCH_FLAG),
            Frame.default(),
            Frame.default(flags=Spec.APPROVE_PAYMENT),
        ],
        None,
        id="approval_scope_after_batch_terminator",
    ),
    pytest.param(
        # Each frame's gas limit fits into 64 bits, but the total
        # frame gas must as well.
        # Execution gas this large also exceeds the EIP-7825 cap, which
        # a client may check first. The budgets also exceed the block's
        # gas capacity, but that check depends on the block, so it
        # follows static validity.
        [
            Frame.verify(),
            Frame.default(gas_limit=2**64 - 1),
        ],
        [
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        ],
        id="frame_gas_sum_overflows",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
    pytest.param(
        # The total sums both dimensions, so a state budget drives
        # the same overflow. The budgets also exceed the block's gas
        # capacity, but that check depends on the block, so it follows
        # static validity.
        [
            Frame.verify(),
            Frame.default(state_gas_limit=2**64 - 1),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_state_gas_sum_overflows",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
    pytest.param(
        # Each dimension's budget fits into 64 bits on its own; only
        # their cross-dimension sum overflows. The execution total also
        # exceeds the EIP-7825 cap, which a client may check first. The
        # budgets also exceed the block's gas capacity, but that check
        # depends on the block, so it follows static validity.
        [
            Frame.verify(),
            Frame.default(gas_limit=2**63, state_gas_limit=2**63),
        ],
        [
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        ],
        id="frame_gas_cross_dimension_sum_overflows",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
    pytest.param(
        # As above, but the execution total stays within the EIP-7825
        # cap, which state gas is exempt from, so the sum overflow is
        # the only static rule broken. Each frame's budgets fit into 64
        # bits on their own; only the running total across both frames
        # reaches exactly 2**64, one past the largest 64-bit value.
        # The budgets also exceed the block's gas capacity, but that check
        # depends on the block, so it follows static validity.
        [
            Frame.verify(gas_limit=2**20, state_gas_limit=0),
            Frame.default(gas_limit=0, state_gas_limit=2**64 - 2**20),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_gas_cross_dimension_sum_overflows_within_gas_cap",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
    # Decode-time rejections: field values outside their type's
    # domain never construct, so the transaction never decodes.
    pytest.param(
        [Frame.verify(), Frame(mode=3)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_frame_mode",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame(mode=255)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="undefined_frame_mode_high",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame.default(flags=0x08)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flag",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame.default(flags=0xFF)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flag_high",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only the reserved bits, so the approval and atomic batch bits
        # break no other rule.
        [Frame.verify(), Frame.default(flags=0xF8)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flags_only",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only the highest bit, which stays reserved should lower bits
        # gain a meaning.
        [Frame.verify(), Frame.default(flags=0x80)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="reserved_frame_flag_top_bit",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Execution gas this large also exceeds the EIP-7825 cap, which
        # a client may check first.
        [Frame.verify(), Frame.default(gas_limit=2**64)],
        [
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        ],
        id="frame_gas_above_64_bits",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
    pytest.param(
        [Frame.verify(), Frame.default(state_gas_limit=2**64)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="frame_state_gas_above_64_bits",
        marks=[
            pytest.mark.exception_test,
            pytest.mark.execute(
                pytest.mark.skip(
                    reason="declared frame budgets near 2**64 require a "
                    "max_fee far beyond what execute mode can fund"
                )
            ),
        ],
    ),
]
"""
Frame-list variations of a minimal frame transaction, each with the
exception it must be rejected with, or `None` where the variation is
the nearest-valid counterpart of a rejected case.
"""


def covering_max_fee(fork: Fork, sender: EOA, frames: List[Frame]) -> int:
    """
    Return the default `max_fee`, raised to the fee the frames' declared
    budgets require, so the fee budget check never adds a second reason
    to reject a case.
    """
    return max(
        TransactionDefaults.max_fee,
        fee_budget(fork, sender, frames).required_max_fee,
    )


@pytest.mark.parametrize("frames,error", FRAME_CASES)
def test_frame_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: TransactionException | List[TransactionException] | None,
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
    frame_list = frames(pre, sender) if callable(frames) else frames
    tx = Transaction(
        sender=sender,
        frames=frame_list,
        max_fee=covering_max_fee(fork, sender, frame_list),
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
    fork: Fork,
    frames: Union[List[Frame], Callable[[Alloc, Address], List[Frame]]],
    error: TransactionException | List[TransactionException] | None,
) -> None:
    """
    Assert the same per-frame rules as `test_frame_constraints` on the
    transaction itself rather than on a block containing it; see the
    module docstring for why every static case fills both formats.
    """
    sender = pre.fund_eoa()
    frame_list = frames(pre, sender) if callable(frames) else frames
    tx = Transaction(
        sender=sender,
        frames=frame_list,
        max_fee=covering_max_fee(fork, sender, frame_list),
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


EXPIRY_VERIFIER_CASES = [
    pytest.param(
        [Frame.verify(), Frame.expiry(data=b"")],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_empty",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame.expiry(data=b"\xff" * 7)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame.expiry(data=b"\xff" * 9)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_data_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [Frame.verify(), Frame.expiry(flags=Spec.APPROVE_PAYMENT)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_flags",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Execution approval must also target the sender, so the target
        # rule rejects this case too; `expiry_frame_with_flags` is the
        # case that isolates the expiry verifier's flags rule.
        [Frame.verify(), Frame.expiry(flags=Spec.APPROVE_EXECUTION)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_execution_flag",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # As above, the target rule rejects this case too.
        [
            Frame.verify(),
            Frame.expiry(flags=Spec.APPROVE_EXECUTION_AND_PAYMENT),
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_execution_and_payment_flags",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The expiry verifier creates no state, so its frame must
        # declare no state gas budget.
        [Frame.verify(), Frame.expiry(state_gas_limit=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="expiry_frame_with_state_gas",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Each frame on its own is well-formed; only their
        # multiplicity violates the rule.
        [Frame.verify(), Frame.expiry(), Frame.expiry()],
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
            Frame.verify(),
            Frame.default(target=Spec.EXPIRY_VERIFIER, data=b"\xff" * 7),
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
            Frame.verify(),
            Frame.verify(
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


CUSTOM_VERIFIER_CODE = Op.STOP
"""
Code of a custom contract verifier accepting every witness, deployed for
the cases a claim on it is statically valid in.
"""


def custom_claim(verifier: Address, **overrides: Any) -> Claim:
    """
    Return a claim of the custom contract `verifier` over `DIGEST` with
    an empty witness and room for the verifier's cold access, overridden
    field by field.
    """
    fields: Dict[str, Any] = dict(
        verifier=verifier,
        msg=Bytes(DIGEST),
        gas_limit=10_000,
        witness=Bytes(b""),
    )
    fields.update(overrides)
    return Claim(**fields)


CLAIM_CASES = [
    pytest.param(
        lambda _pre, sender: [signed_digest_claim(sender.key)],
        None,
        id="secp256k1_digest_claim",
    ),
    # Keys. An empty key resolves to the sender; a 20-byte key is an
    # address; a 32-byte key is used as is.
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(
                sender.key, key=Bytes(bytes(12) + bytes(sender))
            )
        ],
        None,
        id="secp256k1_address_as_32_byte_key",
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, key=Bytes(b"\x01" * 19))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_19_bytes",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, key=Bytes(b"\x01" * 21))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_21_bytes",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                key=Bytes(b"\x01" * 33),
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_33_bytes",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, key=Bytes(bytes(20)))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_zero_address",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                key=Bytes(bytes(32)),
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="key_zero_word",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A secp256k1 or P-256 key is an address: its resolved key leaves
        # the upper 12 bytes clear.
        lambda _pre, sender: [
            signed_digest_claim(
                sender.key, key=Bytes(b"\x01" + bytes(11) + bytes(sender))
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="secp256k1_key_not_an_address",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(b"\x01" * 32),
                msg=Bytes(DIGEST),
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="p256_key_not_an_address",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # Only the address-keyed protocol verifiers restrict the key.
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                key=Bytes(b"\x01" * 32),
            )
        ],
        None,
        id="custom_verifier_32_byte_key",
    ),
    # Messages.
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, msg=Bytes(b"\x01"))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_single_byte",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, msg=Bytes(b"\x01" * 31))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key, msg=Bytes(b"\x01" * 33))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The all-zero digest is reserved as the EVM-visible
        # representation of the canonical-hash case.
        lambda _pre, sender: [
            signed_digest_claim(sender.key, msg=Bytes(bytes(32)))
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="msg_all_zeros",
        marks=pytest.mark.exception_test,
    ),
    # Gas limit and witness length: fixed for protocol verifiers,
    # declared for custom ones.
    pytest.param(
        lambda _pre, sender: [signed_digest_claim(sender.key, gas_limit=1)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="protocol_verifier_with_gas_limit",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [signed_digest_claim(sender.key, witness_len=65)],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="protocol_verifier_with_witness_len",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Claim(
                verifier=Spec.LEANSPHINCS_VERIFIER,
                key=Bytes(b"\x01" * 32),
                gas_limit=Spec.LEANSPHINCS_VERIFICATION_GAS,
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="leansphincs_verifier_with_gas_limit",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE), gas_limit=0
            )
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="custom_verifier_without_gas",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The witness cap sits above what the transaction gas cap can
        # pay for, so the cap rejects the claim too.
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                witness_len=Spec.MAX_CLAIM_WITNESS_BYTES + 1,
                witness=Bytes(bytes(Spec.MAX_CLAIM_WITNESS_BYTES + 1)),
            )
        ],
        [
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        ],
        id="custom_witness_len_above_max",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The total claim gas must fit in 64 bits; it also exceeds the
        # transaction gas cap.
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                gas_limit=2**63,
            ),
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                gas_limit=2**63,
            ),
        ],
        [
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        ],
        id="total_claim_gas_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The largest total claim gas, the sender's claim included,
        # which only the transaction gas cap rejects.
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=CUSTOM_VERIFIER_CODE),
                gas_limit=2**64 - 1 - Spec.SECP256K1_VERIFICATION_GAS,
            ),
        ],
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        id="total_claim_gas_at_max",
        marks=pytest.mark.exception_test,
    ),
    # Claim count.
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key) for _ in range(Spec.MAX_CLAIMS - 1)
        ],
        None,
        id="claim_count_at_max",
    ),
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key) for _ in range(Spec.MAX_CLAIMS)
        ],
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="claim_count_above_max",
        marks=pytest.mark.exception_test,
    ),
]
"""
Variations of the claims of a minimal frame transaction, appended after
the sender's claim consumed by its default code, each with the exception
the transaction must be rejected with, or `None` where the variation is
the nearest-valid counterpart of a rejected case. Every rule here is
decidable from the transaction body; the rules its witnesses must
satisfy are in `test_claims.py`.
"""

ClaimCase = Union[List[Claim], Callable[[Alloc, EOA], List[Claim]]]


@pytest.mark.parametrize("claims,error", CLAIM_CASES)
def test_claim_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    claims: ClaimCase,
    error: Optional[TransactionException | List[TransactionException]],
) -> None:
    """
    Vary the claims of a minimal frame transaction and check that the
    static claim rules reject the transaction, or accept the
    nearest-valid variant.

    The varied claims are appended after the sender's claim consumed by
    its default code, so every case differs from a valid transaction
    only in the appended claims.
    """
    sender = pre.fund_eoa()
    case_claims = claims(pre, sender) if callable(claims) else claims
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, *case_claims],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.parametrize("claims,error", CLAIM_CASES)
def test_claim_constraints_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    claims: ClaimCase,
    error: Optional[TransactionException | List[TransactionException]],
) -> None:
    """
    Assert the same claim rules as `test_claim_constraints` on the
    transaction itself rather than on a block containing it; see the
    module docstring for why every static case fills both formats.
    """
    sender = pre.fund_eoa()
    case_claims = claims(pre, sender) if callable(claims) else claims
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, *case_claims],
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


# The gas boundary tests use a contract sender: contract senders carry
# no claims, so the transaction's intrinsic cost reduces to
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
    # A contract sender carries no claims and the frame no
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
        frames=[Frame.verify(gas_limit=cap - intrinsic + cap_excess)],
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
        frames=[Frame.verify(gas_limit=cap - intrinsic + cap_excess)],
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
        frames=[Frame.verify(gas_limit=cap - intrinsic, state_gas_limit=cap)],
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
        frames=[Frame.verify(gas_limit=cap - intrinsic, state_gas_limit=cap)],
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
            Frame.verify(),
            Frame.default(gas_limit=0, data=Bytes(b"\x00" * data_length)),
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
            Frame.verify(),
            Frame.default(gas_limit=0, data=Bytes(b"\x00" * data_length)),
        ],
        error=error,
    )

    transaction_test(pre=pre, tx=tx)
