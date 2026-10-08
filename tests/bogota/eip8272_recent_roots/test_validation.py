"""
Tests for the validation operation of
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272).

A recent root verifier frame is a `VERIFY` frame targeting the recent root
contract with one to sixteen 72-byte tuples. The contract checks every
tuple's slot against the current slot and its entry hash against storage;
a failing check reverts, which for a `VERIFY` frame invalidates the whole
transaction. Every case seeds the contract's storage directly, so the
checks are exercised against known entries.
"""

from typing import Dict, List, Sequence

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import (
    expiry_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .helpers import recent_root_frame, validation_gas
from .spec import (
    Spec,
    entry_hash,
    ref_spec_8272,
    source_id,
    storage_key,
    validation_tuple,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

CURRENT_SLOT = 10_000
"""Slot of the block executing the frame transaction."""

SALT = bytes(32)
"""Salt of every root source in these tests."""

INVALID_FRAME_EXECUTION = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION


def seeded_entries(
    references: Sequence[tuple[bytes, int, bytes]],
) -> Dict[int, int]:
    """
    Return the storage seeding the entries of `(source_id, slot, root)`
    references at the recent root contract.
    """
    return {
        storage_key(source, slot): int.from_bytes(
            entry_hash(source, slot, root), "big"
        )
        for source, slot, root in references
    }


def install_entries(pre: Alloc, storage: Dict[int, int]) -> None:
    """Seed the recent root contract's storage with `storage`."""
    pre[Spec.RECENT_ROOT_ADDRESS] = Account(
        nonce=Spec.RECENT_ROOT_NONCE,
        code=Spec.RECENT_ROOT_CODE,
        storage=storage,
    )


def root_of(index: int) -> bytes:
    """Return a distinct 32-byte root for `index`."""
    return (0xA000 + index).to_bytes(32, "big")


def run_verifier(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    *,
    frames: List[Frame],
    verifier_gas: int | None,
    error: TransactionException | None = None,
    verifier_index: int = 0,
    current_slot: int = CURRENT_SLOT,
) -> None:
    """
    Execute `frames` followed by an approving frame and a sender frame
    that records execution, pinning the verifier frame's gas when the
    transaction is valid.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    all_frames = frames + [verify_frame(), sender_frame(target=target)]

    expected_receipt = None
    if error is None:
        frame_receipts = [
            FrameReceipt(status=FrameSpec.STATUS_SUCCESS) for _ in all_frames
        ]
        if verifier_gas is not None:
            frame_receipts[verifier_index] = FrameReceipt(
                status=FrameSpec.STATUS_SUCCESS,
                gas_used=verifier_gas,
                state_gas_used=0,
            )
        expected_receipt = TransactionReceipt(
            payer=sender, frame_receipts=frame_receipts
        )

    state_test(
        env=Environment(slot_number=current_slot),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=all_frames,
            error=error,
            expected_receipt=expected_receipt,
        ),
        post={
            target: Account(storage={SLOT_EXECUTED: 0 if error else 1}),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "sources,repeats",
    [
        pytest.param(1, 1, id="one_tuple"),
        pytest.param(16, 1, id="sixteen_distinct_tuples"),
        pytest.param(1, 2, id="duplicate_tuple"),
        pytest.param(1, 16, id="sixteen_copies_of_one_tuple"),
        pytest.param(8, 2, id="eight_tuples_each_twice"),
    ],
)
def test_valid_references(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sources: int,
    repeats: int,
) -> None:
    """
    Verify valid references from the previous slot: distinct sources read
    distinct cold storage keys, and repeated tuples are checked again
    against keys that are then warm. The frame's gas pins the cold target
    access at entry, the contract's execution and one storage read per
    tuple.
    """
    slot = CURRENT_SLOT - 1
    references = [
        (source_id(pre.fund_eoa(amount=0), SALT), slot, root_of(index))
        for index in range(sources)
    ]
    install_entries(pre, seeded_entries(references))
    tuples = [
        validation_tuple(*reference)
        for reference in references
        for _ in range(repeats)
    ]

    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(tuples)],
        verifier_gas=validation_gas(
            fork, tuples=len(tuples), cold_keys=sources
        ),
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "seeded_slot,referenced_slot,root_offset,source_offset",
    [
        pytest.param(
            CURRENT_SLOT - 1, CURRENT_SLOT - 1, 1, 0, id="wrong_root"
        ),
        pytest.param(
            CURRENT_SLOT - 1, CURRENT_SLOT - 1, 0, 1, id="wrong_source"
        ),
        pytest.param(
            CURRENT_SLOT - 2, CURRENT_SLOT - 1, 0, 0, id="wrong_slot"
        ),
        pytest.param(
            CURRENT_SLOT - 1 - Spec.RECENT_ROOT_LENGTH,
            CURRENT_SLOT - 1,
            0,
            0,
            id="stale_occupant_of_same_ring_index",
        ),
        pytest.param(CURRENT_SLOT, CURRENT_SLOT, 0, 0, id="current_slot"),
        pytest.param(
            CURRENT_SLOT + 1, CURRENT_SLOT + 1, 0, 0, id="future_slot"
        ),
        pytest.param(
            CURRENT_SLOT - Spec.RECENT_ROOT_LENGTH,
            CURRENT_SLOT - Spec.RECENT_ROOT_LENGTH,
            0,
            0,
            id="expired_reference",
        ),
    ],
)
@pytest.mark.exception_test
def test_invalid_reference(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    seeded_slot: int,
    referenced_slot: int,
    root_offset: int,
    source_offset: int,
) -> None:
    """
    Reject a reference whose tuple does not match a stored entry, whose
    slot is the current or a future slot, or whose root is
    `RECENT_ROOT_LENGTH` slots old.

    The expired case stores the entry under the key its slot maps to; the
    contract rejects it on age alone, so a root the ring buffer would
    overwrite in the current slot is never referenceable. The current and
    future slot cases likewise store their entries, so only the slot
    checks reject them.
    """
    source_address = pre.fund_eoa(amount=0)
    other_address = pre.fund_eoa(amount=0)
    source = source_id(source_address, SALT)
    referenced_source = source_id(
        other_address if source_offset else source_address, SALT
    )
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, seeded_slot, root)]))
    reference = validation_tuple(
        referenced_source, referenced_slot, root_of(root_offset)
    )

    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(reference)],
        verifier_gas=None,
        error=INVALID_FRAME_EXECUTION,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "age,error",
    [
        pytest.param(
            Spec.RECENT_ROOT_USABLE_WINDOW, None, id="usable_window_edge"
        ),
        pytest.param(
            Spec.RECENT_ROOT_USABLE_WINDOW + 1,
            INVALID_FRAME_EXECUTION,
            id="one_slot_past_window",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_age_window(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    age: int,
    error: TransactionException | None,
) -> None:
    """
    Accept a root exactly `RECENT_ROOT_USABLE_WINDOW` slots old and
    reject one slot older, with the entry stored in both cases.
    """
    slot = CURRENT_SLOT - age
    source = source_id(pre.fund_eoa(amount=0), SALT)
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, slot, root)]))

    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(validation_tuple(source, slot, root))],
        verifier_gas=validation_gas(fork, tuples=1, cold_keys=1),
        error=error,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "data_length",
    [
        pytest.param(0, id="empty_data"),
        pytest.param(Spec.RECENT_ROOT_TUPLE_BYTES - 1, id="71_bytes"),
        pytest.param(Spec.RECENT_ROOT_TUPLE_BYTES + 1, id="73_bytes"),
        pytest.param(
            (Spec.MAX_RECENT_ROOT_REFERENCES + 1)
            * Spec.RECENT_ROOT_TUPLE_BYTES,
            id="seventeen_tuples",
        ),
    ],
)
@pytest.mark.exception_test
def test_invalid_data_length(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    data_length: int,
) -> None:
    """
    Reject validation calldata that is empty, not a whole number of
    tuples, or more than sixteen tuples, even when every whole tuple in
    it would validate.
    """
    slot = CURRENT_SLOT - 1
    source = source_id(pre.fund_eoa(amount=0), SALT)
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, slot, root)]))
    tuple_bytes = validation_tuple(source, slot, root)
    repeated = tuple_bytes * (data_length // Spec.RECENT_ROOT_TUPLE_BYTES + 1)

    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(repeated[:data_length])],
        verifier_gas=None,
        error=INVALID_FRAME_EXECUTION,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "overrides,error",
    [
        pytest.param(
            {"flags": FrameSpec.APPROVE_PAYMENT}, None, id="payment_flag"
        ),
        pytest.param(
            {"state_gas_limit": 1_000}, None, id="nonzero_state_gas_limit"
        ),
        pytest.param(
            {"flags": FrameSpec.ATOMIC_BATCH_FLAG},
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="atomic_batch_flag",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            {"value": 1},
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="nonzero_value",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_frame_shape_variants(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    overrides: Dict[str, int],
    error: TransactionException | None,
) -> None:
    """
    Frames that differ from the canonical verifier frame in one field.

    A payment approval flag or a nonzero state gas budget leaves block
    validity untouched: the contract executes normally and succeeds (the
    public mempool would not classify such a frame as a recent root
    verifier). A `VERIFY` frame carrying value is statically invalid
    under EIP-8141 before any frame runs.
    """
    slot = CURRENT_SLOT - 1
    source = source_id(pre.fund_eoa(amount=0), SALT)
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, slot, root)]))
    verifier = recent_root_frame(
        validation_tuple(source, slot, root), **overrides
    )

    run_verifier(
        state_test,
        pre,
        fork,
        frames=[verifier],
        verifier_gas=validation_gas(fork, tuples=1, cold_keys=1),
        error=error,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "gas_offset,error",
    [
        pytest.param(0, None, id="exact_gas"),
        pytest.param(
            -1,
            INVALID_FRAME_EXECUTION,
            id="one_gas_short",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.parametrize(
    "sources,repeats",
    [
        (1, 1),
        (Spec.MAX_RECENT_ROOT_REFERENCES, 1),
        (1, Spec.MAX_RECENT_ROOT_REFERENCES),
    ],
    ids=["one_tuple", "distinct_tuples", "duplicate_tuples"],
)
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_execution_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_offset: int,
    error: TransactionException | None,
    sources: int,
    repeats: int,
    warm: bool,
) -> None:
    """Pin exact and one-short gas with cold, repeated and warm reads."""
    slot = CURRENT_SLOT - 1
    references = [
        (source_id(pre.fund_eoa(amount=0), SALT), slot, root_of(index))
        for index in range(sources)
    ]
    install_entries(pre, seeded_entries(references))
    tuples = [
        validation_tuple(*reference) for reference in references
    ] * repeats
    required = validation_gas(
        fork,
        tuples=len(tuples),
        cold_keys=0 if warm else sources,
        target_warm=warm,
    )
    verifier = recent_root_frame(tuples, gas_limit=required + gas_offset)
    # A preceding verifier warms both the target and every referenced key.
    # Multiple matching verifier frames are valid in a block.
    frames = [recent_root_frame(tuples), verifier] if warm else [verifier]

    run_verifier(
        state_test,
        pre,
        fork,
        frames=frames,
        verifier_gas=required,
        verifier_index=1 if warm else 0,
        error=error,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "position",
    [
        pytest.param("after_expiry", id="after_expiry_verifier"),
        pytest.param("last", id="after_account_validation"),
    ],
)
def test_frame_position(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    position: str,
) -> None:
    """
    The verifier frame executes the same wherever it sits in the frame
    list: after an expiry verifier frame in the public mempool's
    canonical order, or after account validation and execution, where
    the public mempool would reject the shape but a block accepts it.
    """
    slot = CURRENT_SLOT - 1
    source = source_id(pre.fund_eoa(amount=0), SALT)
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, slot, root)]))
    verifier = recent_root_frame(validation_tuple(source, slot, root))
    verifier_gas = validation_gas(fork, tuples=1, cold_keys=1)

    if position == "after_expiry":
        run_verifier(
            state_test,
            pre,
            fork,
            frames=[expiry_frame(), verifier],
            verifier_gas=verifier_gas,
            verifier_index=1,
        )
        return

    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    state_test(
        env=Environment(slot_number=CURRENT_SLOT),
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[verify_frame(), sender_frame(target=target), verifier],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                    FrameReceipt(
                        status=FrameSpec.STATUS_SUCCESS,
                        gas_used=verifier_gas,
                        state_gas_used=0,
                    ),
                ],
            ),
        ),
        post={target: Account(storage={SLOT_EXECUTED: 1})},
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("bad_index", [0, 7, 15])
@pytest.mark.exception_test
def test_invalid_tuple_in_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    bad_index: int,
) -> None:
    """Reject the whole verification even when earlier tuples passed."""
    source = source_id(pre.fund_eoa(amount=0), SALT)
    slot = CURRENT_SLOT - 1
    root = root_of(0)
    install_entries(pre, seeded_entries([(source, slot, root)]))
    tuples = [
        validation_tuple(source, slot, root)
    ] * Spec.MAX_RECENT_ROOT_REFERENCES
    tuples[bad_index] = validation_tuple(source, slot, root_of(1))
    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(tuples)],
        verifier_gas=None,
        error=INVALID_FRAME_EXECUTION,
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("slot", [0, 2**32, 2**64 - 2])
def test_full_width_slot_and_zero_root(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slot: int,
) -> None:
    """Validate the full uint64 slot encoding and an opaque zero root."""
    source = source_id(pre.fund_eoa(amount=0), SALT)
    root = bytes(32)
    install_entries(pre, seeded_entries([(source, slot, root)]))
    run_verifier(
        state_test,
        pre,
        fork,
        frames=[recent_root_frame(validation_tuple(source, slot, root))],
        verifier_gas=validation_gas(fork, tuples=1, cold_keys=1),
        current_slot=slot + 1,
    )
