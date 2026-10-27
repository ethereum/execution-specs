"""
Transaction-level gas settlement tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction's payer-facing `gas_used` is the post-refund execution
usage held to the EIP-7976 calldata floor plus final attributed state gas.
Block accounting keeps the same state dimension but counts execution before
storage refunds, as required by EIP-7778.

Storage refunds accumulate across frames into one signed,
transaction-scoped counter, and a failed frame's changes to it are
discarded. The refund cap's base counts both dimensions, while a
state-gas refill has already left the receipts and no cap touches it.
Because the block counts execution before the refund, a refund lowers
what the payer pays without freeing block capacity.

A storage refill that a frame rollback returns to its owner — by an
atomic batch unroll or by the refilling frame's own revert — lands back
in the spent gas, not only in the restored per-frame receipt. The
state-dimension halves of those rollback scenarios are pinned in
`test_state_gas.py`.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.base_types import HexNumber, StorageRootType

from .helpers import (
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    floor_binding_padding,
    padding_frame,
    reservation_block,
    reservation_error,
    reserving_frame_tx,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CREATED = 0x01
"""
Storage slot the worker contract creates, clears, or returns to its
transaction-start value.
"""

SLOT_OWNER_USED = 0x06
"""Probe slot recording the creating frame's restored state gas attribution."""

SLOT_STATUS = 0x08
"""
Probe slot recording the rolled-back frame's receipt status, plus one so
the expected `FAILURE` readback is distinguishable from a slot never
written.
"""

PADDING_READS = 400
"""
Warm balance reads padding a transaction, so a fifth of its gas covers
the refunds the test expects to apply in full.
"""


@pytest.mark.parametrize(
    "with_state_write",
    [
        pytest.param(True, id="state_write"),
        pytest.param(False, id="no_state_write"),
    ],
)
@pytest.mark.parametrize(
    "floor_bound", [True, False], ids=["floor", "below_floor"]
)
@pytest.mark.parametrize(
    "sender_kind",
    [
        pytest.param("eoa", id="eoa_sender"),
        pytest.param("contract", id="contract_sender"),
    ],
)
def test_calldata_floor_with_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    with_state_write: bool,
    floor_bound: bool,
    sender_kind: str,
) -> None:
    """
    Bind the calldata floor on a transaction that also grows state.

    The floor is compared against the execution dimension alone, so a
    floor-bound transaction pays the floor plus its state gas in full:
    state growth never rides free under the data floor. The frame data
    is the fewest bytes that bind the floor, or one byte less in
    `below_floor`, where the execution dimension binds again. An EOA
    sender's signature bytes count toward the floor, while a contract
    sender carries none.
    """
    sender: Address
    if sender_kind == "eoa":
        sender = pre.fund_eoa()
        nonce = 0
        # The default code approves without drawing execution gas.
        verify_code = Bytecode()
    else:
        verify_code = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
        sender = pre.deploy_contract(code=verify_code, balance=10**18)
        nonce = 1
    write = Op.SSTORE(
        SLOT_CREATED, 1, key_warm=False, original_value=0, new_value=1
    )
    # Pad execution so the signature bytes alone never bind the floor.
    # The sender seeds the warm set, so its balance reads are warm.
    padding = Op.POP(Op.BALANCE(address=sender, address_warm=True)) * 20
    worker_code = (
        padding + (write if with_state_write else Bytecode()) + Op.STOP
    )
    worker = pre.deploy_contract(code=worker_code)

    def build(data_length: int) -> FrameTransaction:
        """Return the transaction carrying `data_length` padding bytes."""
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=nonce,
            # Each frame is budgeted exactly what it spends, so the
            # execution dimension is known to the byte.
            frames=[
                verify_frame(
                    code=verify_code,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                default_frame(
                    target=worker,
                    code=worker_code,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                    data=bytes(data_length),
                ),
            ],
        )

    def floor_binds(data_length: int) -> bool:
        return build(data_length).floor_binds()

    data_length = floor_binding_padding(floor_binds)
    if not floor_bound:
        data_length -= 1
    tx = build(data_length)
    # The premise of the test: the floor binds, or in `below_floor`
    # falls short by the last byte.
    assert tx.floor_binds() == floor_bound

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=nonce + 1),
            worker: Account(
                storage={SLOT_CREATED: 1 if with_state_write else 0}
            ),
        },
    )


CLEARED_SLOTS = (1, 2, 3, 4)
"""Pre-existing slots holding one, each cleared for a clearing refund."""

CLEARED_STORAGE: StorageRootType = dict.fromkeys(CLEARED_SLOTS, 1)
"""Pre-state storage of a worker clearing `CLEARED_SLOTS`."""

FRESH_SLOT_BASE = 0x100
"""First of the fresh slots a frame creates next to its clears."""


def clear(slot: int) -> Bytecode:
    """Return a cold write clearing `slot`, which holds one."""
    return Op.SSTORE(
        slot,
        0,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )


def worker_write(
    *, key_warm: bool, original: int, current: int, new: int
) -> Bytecode:
    """
    Return the worker's write of its frame's data word into
    `SLOT_CREATED`, priced for the given values.
    """
    return Op.SSTORE(
        SLOT_CREATED,
        Op.CALLDATALOAD(0),
        key_warm=key_warm,
        original_value=original,
        current_value=current,
        new_value=new,
    )


def word(value: int) -> bytes:
    """Return `value` as the 32-byte data word a worker writes."""
    return value.to_bytes(32, "big")


def sender_padding_frame(pre: Alloc, sender: Address) -> FrameCase:
    """
    Return a frame spending execution gas on warm reads of the sender,
    which seeds the warm set, and nothing else.
    """
    return padding_frame(
        pre,
        Op.POP(Op.BALANCE(address=sender, address_warm=True)) * PADDING_READS,
        gas_limit_delta=0,
        state_gas_limit=0,
    )


@pytest.mark.parametrize(
    "boundary,floor_side",
    [
        pytest.param(
            "post_refund", "below", id="floor_just_below_post_refund"
        ),
        pytest.param(
            "post_refund", "above", id="floor_just_above_post_refund"
        ),
        pytest.param("pre_refund", "below", id="floor_just_below_pre_refund"),
        pytest.param("pre_refund", "above", id="floor_just_above_pre_refund"),
    ],
)
def test_storage_refund_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    boundary: str,
    floor_side: str,
) -> None:
    """
    Settle a frame transaction that clears a pre-existing storage slot.

    The cases pin both settlement clamps around the calldata floor:
    payer-facing gas uses post-refund execution while block execution gas
    remains pre-refund under EIP-7778. The frame data is the fewest bytes
    that lift the floor above the post-refund or the pre-refund execution
    gas, or one byte less. Clearing durable state consumes no state gas,
    so the frame declares none.
    """
    sender = pre.fund_eoa()
    # Pad execution so the refund cap — a fifth of the pre-refund
    # usage — stays above the clearing refund and the refund applies
    # in full. The sender seeds the warm set, so its repeated balance
    # reads are warm accesses.
    padding = (
        Op.POP(Op.BALANCE(address=sender, address_warm=True)) * PADDING_READS
    )
    worker_code = padding + clear(SLOT_CREATED) + Op.STOP
    worker = pre.deploy_contract(code=worker_code, storage={SLOT_CREATED: 1})
    refund = worker_code.refund(fork)

    def build(data_length: int) -> FrameTransaction:
        """Return the transaction carrying `data_length` padding bytes."""
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=0,
            refund=refund,
            frames=[
                verify_frame(),
                # The receipt reports pre-refund execution gas; the
                # refund applies only at transaction settlement.
                default_frame(
                    target=worker,
                    code=worker_code,
                    state_gas_limit=0,
                    data=bytes(data_length),
                ),
            ],
        )

    def floor_binds(data_length: int) -> bool:
        return build(data_length).floor_binds(
            after_refund=boundary == "post_refund"
        )

    data_length = floor_binding_padding(floor_binds)
    if floor_side == "below":
        data_length -= 1
    tx = build(data_length)
    # The premise of the test: the refund applies uncapped.
    assert 0 < tx.effective_refund == refund
    gas_used_after_refund = tx.gas_before_refund - refund
    # The premise of each case: the floor sits below the post-refund
    # gas, above the pre-refund gas, or between the two.
    if (boundary, floor_side) == ("post_refund", "below"):
        assert tx.calldata_floor < gas_used_after_refund
    elif (boundary, floor_side) == ("pre_refund", "above"):
        assert tx.gas_before_refund < tx.calldata_floor
    else:
        assert gas_used_after_refund < tx.calldata_floor < tx.gas_before_refund

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0}),
        },
        blockchain_test_header_verify=Header(gas_used=tx.block_gas_used()),
    )


@pytest.mark.parametrize(
    "fresh_slots,refilled",
    [
        pytest.param(0, False, id="no_state_gas"),
        pytest.param(1, False, id="one_fresh_slot"),
        pytest.param(2, False, id="two_fresh_slots"),
        pytest.param(1, True, id="one_fresh_slot_refilled"),
    ],
)
def test_refund_cap_base_includes_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    fresh_slots: int,
    refilled: bool,
) -> None:
    """
    Cap the storage refund at a fifth of the gas used before refunds,
    state gas included.

    EIP-8141 "Transaction settlement": "`gas_used_before_refund =
    standard_gas_limit - tx_unused_gas`; `applied_refund =
    min(refund_counter, gas_used_before_refund // MAX_REFUND_QUOTIENT)`",
    where `tx_unused_gas` sums both pools, so the base counts both
    dimensions.

    One frame clears four slots, a refund far above a fifth of its
    small execution, and creates `fresh_slots` slots. Without state gas
    the cap binds on the execution alone. One created slot lifts the
    cap by a fifth of its state gas, still binding; two lift it above
    the refund, which then applies in full, where a cap on execution
    alone would still bind. A created slot cleared again in the same
    frame is refilled before settlement, so it leaves the base and adds
    its write's restoring refund.
    """
    sender = pre.fund_eoa()
    code = sum((clear(slot) for slot in CLEARED_SLOTS), Bytecode())
    for index in range(fresh_slots):
        code += Op.SSTORE(FRESH_SLOT_BASE + index, 1)
    if refilled:
        code += Op.SSTORE(
            FRESH_SLOT_BASE,
            0,
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )
    code += Op.STOP
    worker = pre.deploy_contract(code=code, storage=CLEARED_STORAGE)
    # A refilled slot's state refund returns its state gas to the frame's
    # receipt rather than entering the refund counter.
    refund = code.refund(fork) - code.state_refund(fork)
    state_gas = code.state_cost(fork) - code.state_refund(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=code,
                state_gas_limit=code.state_cost(fork),
                state_gas_used=state_gas,
            ),
        ],
    )
    quotient = fork.max_refund_quotient()
    execution_cap = (tx.gas_before_refund - tx.state_gas) // quotient
    # The premises: the floor does not bind, and the refund is capped on
    # both dimensions, binding unless two slots lift the cap above it,
    # where a cap on execution alone would still bind.
    assert tx.state_gas == state_gas
    assert not tx.floor_binds()
    assert (tx.effective_refund < refund) == (fresh_slots < 2 or refilled)
    assert refund > execution_cap
    if state_gas:
        assert tx.effective_refund > execution_cap

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(
                storage={
                    FRESH_SLOT_BASE + index: 0 if refilled else 1
                    for index in range(fresh_slots)
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "second_write,second_outcome",
    [
        pytest.param(1, Outcome.SUCCESS, id="restored"),
        pytest.param(2, Outcome.SUCCESS, id="rewritten"),
        pytest.param(1, Outcome.REVERT, id="restored_then_reverted"),
    ],
)
def test_refund_reversed_by_later_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    second_write: int,
    second_outcome: Outcome,
) -> None:
    """
    Reverse, in a later frame, a clearing refund an earlier frame
    earned.

    EIP-8141 "Transaction settlement": "Storage gas refunds
    ([EIP-3529](./eip-3529.md)) accumulate across frames into a single
    transaction-scoped `refund_counter`. Changes made to the counter by
    a reverted frame ... are discarded together with that frame's state
    changes." EIP-8038: `STORAGE_CLEAR_REFUND` "is subtracted if the
    original value is non-zero, the current value is zero and the new
    value is non-zero", and `STORAGE_WRITE` "is refunded if the new
    value equals the original value and differs from the current
    value".

    One frame clears a slot holding one, earning the clearing refund. A
    later frame writes it again: restoring one takes the clearing
    refund back and earns the restoring refund, the later frame's own
    contribution being negative; writing two takes the clearing refund
    back alone, leaving no refund. A later frame that restores the slot
    in a call and then reverts discards its changes, so the clearing
    refund stands. A padding frame keeps the cap above every refund. A
    client keeping an unsigned counter per frame cannot represent the
    later frame's contribution.
    """
    sender = pre.fund_eoa()
    clear_code = (
        worker_write(key_warm=False, original=1, current=1, new=0) + Op.STOP
    )
    worker = pre.deploy_contract(code=clear_code, storage={SLOT_CREATED: 1})
    second_write_code = worker_write(
        key_warm=True, original=1, current=0, new=second_write
    )
    if second_outcome is Outcome.REVERT:
        # A wrapper calls the worker and then reverts the frame.
        wrapper_code = (
            Op.CALLDATACOPY(0, 0, 32, data_size=32, new_memory_size=32)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    # The clearing frame left the worker warm.
                    address=worker,
                    args_offset=0,
                    args_size=32,
                    address_warm=True,
                )
            )
            + Op.REVERT(0, 0)
        )
        second_target = pre.deploy_contract(code=wrapper_code)
        second_warm = False
        second_gas = wrapper_code.execution_cost(
            fork
        ) + second_write_code.execution_cost(fork)
        # The revert discards the second write's change to the counter.
        refund = clear_code.refund(fork)
        final_value = 0
    elif second_outcome is Outcome.SUCCESS:
        second_target = worker
        second_warm = True
        second_gas = second_write_code.execution_cost(fork)
        refund = clear_code.refund(fork) + second_write_code.refund(fork)
        final_value = second_write
    else:
        raise ValueError(f"unknown second_outcome: {second_outcome!r}")

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            sender_padding_frame(pre, sender),
            # Frame 2: clear the slot (1 -> 0).
            default_frame(
                target=worker,
                code=clear_code,
                data=word(0),
                state_gas_limit=0,
            ),
            # Frame 3: write it again (0 -> `second_write`); frame 2's
            # success left the worker and its slot warm.
            default_frame(
                target=second_target,
                execution_gas=second_gas,
                data=word(second_write),
                warm=second_warm,
                state_gas_limit=0,
                outcome=second_outcome,
            ),
        ],
    )
    # The premise: the cap never binds.
    assert tx.effective_refund == refund
    quotient = fork.max_refund_quotient()
    assert clear_code.refund(fork) <= tx.gas_before_refund // quotient

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: final_value}),
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Outcome.REVERT, id="frame_reverts"),
        pytest.param(Outcome.HALT, id="frame_halts"),
    ],
)
def test_failed_frame_discards_clearing_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: Outcome,
) -> None:
    """
    Discard the clearing refund of a frame that fails after earning it.

    EIP-8141 "Transaction settlement": "Changes made to the counter by
    a reverted frame ... are discarded together with that frame's state
    changes", and a frame that halts exceptionally performs "the same
    state-gas restoration" (State-gas attribution and refills).

    The frame clears a slot holding one and then reverts or halts. The
    slot keeps its value and the transaction settles with no refund,
    while a padding frame keeps the cap above the clearing refund, so a
    client keeping the refund charges less. A halting frame's receipt
    cannot tell a halt at `INVALID` from running out of gas before the
    clear; the reverting case pins the gas of the whole path, which
    fits the frame's budget.
    """
    sender = pre.fund_eoa()
    if outcome is Outcome.REVERT:
        ending = Op.REVERT(0, 0)
    elif outcome is Outcome.HALT:
        ending = Op.INVALID
    else:
        raise ValueError(f"unknown outcome: {outcome!r}")
    cleared = clear(SLOT_CREATED)
    code = cleared + ending
    worker = pre.deploy_contract(code=code, storage={SLOT_CREATED: 1})
    failing = default_frame(
        target=worker,
        code=code,
        state_gas_limit=0,
        outcome=outcome,
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(), sender_padding_frame(pre, sender), failing],
    )
    # The premises: the whole path fits the frame's budget, and the cap
    # would let the refund apply in full.
    assert failing.entry_gas(fork) + failing.code_gas(fork) < int(
        failing.gas_limit
    )
    quotient = fork.max_refund_quotient()
    assert cleared.refund(fork) <= tx.gas_before_refund // quotient

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 1}),
        },
    )


def test_refunds_accumulate_across_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Add the clearing refunds of two frames into one counter.

    EIP-8141 "Transaction settlement": "Storage gas refunds
    ([EIP-3529](./eip-3529.md)) accumulate across frames into a single
    transaction-scoped `refund_counter`."

    Two frames each clear a different slot of the same contract. The
    transaction settles with both clearing refunds, the cap kept above
    their sum by two padding frames.
    """
    sender = pre.fund_eoa()
    # Each frame clears the slot its data names, cold.
    clear_code = (
        Op.SSTORE(
            Op.CALLDATALOAD(0),
            0,
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=0,
        )
        + Op.STOP
    )
    worker = pre.deploy_contract(code=clear_code, storage={1: 1, 2: 1})
    # Each of the two clearing frames runs `clear_code` once.
    refund = 2 * clear_code.refund(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            sender_padding_frame(pre, sender),
            sender_padding_frame(pre, sender),
            default_frame(
                target=worker,
                code=clear_code,
                data=word(1),
                state_gas_limit=0,
            ),
            # The first clear left the worker warm, not this slot.
            default_frame(
                target=worker,
                code=clear_code,
                data=word(2),
                warm=True,
                state_gas_limit=0,
            ),
        ],
    )
    # The premise: the cap lets both refunds apply.
    assert tx.effective_refund == refund

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), worker: Account(storage={})},
    )


def test_surviving_refill_is_not_capped(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Remove a cross-frame refill from the gas used before the refund cap
    applies.

    EIP-8141 "Transaction settlement": "Because a state-gas refill
    directly reduces `frame_receipt.gas_used.state`, it reduces
    `gas_used_before_refund` and is not subject to the refund cap."

    One frame creates a slot; a later frame clears it, refilling the
    first frame's receipt to zero state gas and earning the restoring
    refund. The transaction settles with no state gas and the whole
    restoring refund. A client routing the refill through the refund
    counter instead counts the slot's state gas before the refund and
    caps the sum at a fifth of the execution, charging more.
    """
    sender = pre.fund_eoa()
    create_code = (
        worker_write(key_warm=False, original=0, current=0, new=1) + Op.STOP
    )
    worker = pre.deploy_contract(code=create_code)
    refill_code = (
        worker_write(key_warm=True, original=0, current=1, new=0) + Op.STOP
    )
    slot_state_gas = create_code.state_cost(fork)
    # The refill's state refund returns the slot's state gas to the
    # creating frame's receipt; only the rest enters the refund counter.
    refund = refill_code.refund(fork) - refill_code.state_refund(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            sender_padding_frame(pre, sender),
            # Frame 2: create the slot (0 -> 1); frame 3 refills it.
            default_frame(
                target=worker,
                code=create_code,
                data=word(1),
                state_gas_limit=slot_state_gas,
                state_gas_used=0,
            ),
            # Frame 3: clear it (1 -> 0), refilling frame 2's receipt.
            default_frame(
                target=worker,
                code=refill_code,
                data=word(0),
                warm=True,
                state_gas_limit=0,
            ),
        ],
    )
    # The premises: no state gas survives, the refund applies in full,
    # and the slot's state gas exceeds what the cap would allow on top.
    assert tx.state_gas == 0
    assert tx.effective_refund == refund
    quotient = fork.max_refund_quotient()
    assert refund + slot_state_gas > tx.gas_before_refund // quotient

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), worker: Account(storage={})},
    )


def test_batch_unroll_refill_restores_spent_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Settle a transaction whose atomic batch unroll restores a cross-frame
    refill.

    An earlier frame creates a slot; a batch frame returns it to its
    transaction-start value, refilling the creating frame's receipt; the
    batch's terminating frame reverts, unrolling the batch. The unroll
    restores the creating frame's full attribution and re-appends the
    batch frames' receipts with their state gas zeroed. A later frame reads
    the restored attribution back live, and the transaction's spent gas is
    settled from the restored receipts.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    # A passive worker that writes whichever value its frame passes: the
    # creating frame passes one, the refilling frame passes zero.
    worker_code = Op.SSTORE(SLOT_CREATED, Op.CALLDATALOAD(0)) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    reverter_code = Op.REVERT(0, 0)
    reverter = pre.deploy_contract(code=reverter_code)
    probe_code = (
        Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(3, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    create_body = (
        Op.SSTORE(
            SLOT_CREATED,
            Op.CALLDATALOAD(0),
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        + Op.STOP
    )
    refill_body = (
        Op.SSTORE(
            SLOT_CREATED,
            Op.CALLDATALOAD(0),
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )
        + Op.STOP
    )

    # No refund survives to settlement: the only slot returned to its
    # start value is undone by the rollback under test.
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1), keeping its full
            # attribution once the unroll undoes the refill applied to
            # this receipt.
            default_frame(
                target=worker,
                code=create_body,
                data=(1).to_bytes(32, "big"),
            ),
            # Frame 2: open the batch and return the slot to its start
            # value (1 -> 0), refilling frame 1's receipt. The unroll
            # re-appends this receipt with its state gas zeroed.
            # Frame 1's success left the worker warm.
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                code=refill_body,
                warm=True,
                outcome=Outcome.UNROLLED,
            ),
            # Frame 3: terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                code=reverter_code,
                outcome=Outcome.REVERT,
            ),
            # Frame 4: read frame 1's restored attribution and frame 3's
            # status after the unroll.
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The unroll undid the batch frame's clearing write, so the
            # created slot survives.
            worker: Account(storage={SLOT_CREATED: 1}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


def test_frame_revert_refill_restores_spent_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Settle a transaction whose reverting frame restores a cross-frame
    refill.

    An earlier frame creates a slot; a later frame returns it to its
    transaction-start value, refilling the creating frame's receipt, and
    then reverts. The revert's rollback extends over the receipt edit,
    restoring the creating frame's attribution, and the reverting frame's
    own receipt reports zero state gas. A later frame reads the restored
    attribution back live, and the transaction's spent gas is settled from
    the restored receipts.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    # A worker that writes whichever value its frame passes and then
    # reverts when called with empty data: the creating frame passes a
    # value word and stops, the refilling frame passes no data and reverts.
    worker_code = Op.SSTORE(SLOT_CREATED, Op.CALLDATALOAD(0)) + Conditional(
        condition=Op.ISZERO(Op.CALLDATASIZE),
        if_true=Op.REVERT(0, 0),
        if_false=Op.STOP,
    )
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    # The worker's control flow after the store: evaluate the calldata
    # size, then branch. The branch is taken only on the reverting path.
    branch_control = (
        Op.CALLDATASIZE + Op.ISZERO + Op.PUSH1(0) + Op.PC + Op.ADD + Op.JUMPI
    ).execution_cost(fork)
    revert_tail = (
        Op.JUMPDEST + Op.PUSH1(0) + Op.PUSH1(0) + Op.REVERT
    ).execution_cost(fork)
    create_store = Op.SSTORE(
        SLOT_CREATED,
        Op.CALLDATALOAD(0),
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    refill_store = Op.SSTORE(
        SLOT_CREATED,
        Op.CALLDATALOAD(0),
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )

    # No refund survives to settlement: the only slot returned to its
    # start value is undone by the rollback under test.
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1), storing, evaluating the
            # branch and falling through to the trailing stop. The
            # revert restores the refill applied to this receipt.
            default_frame(
                target=worker,
                code=create_store,
                execution_gas=create_store.execution_cost(fork)
                + branch_control,
                data=(1).to_bytes(32, "big"),
            ),
            # Frame 2: return the slot to its start value (1 -> 0),
            # refilling frame 1's receipt, then take the branch into the
            # revert. Frame 1's success left the worker warm.
            default_frame(
                target=worker,
                code=refill_store,
                execution_gas=refill_store.execution_cost(fork)
                + branch_control
                + revert_tail,
                warm=True,
                outcome=Outcome.REVERT,
            ),
            # Frame 3: read frame 1's restored attribution and frame 2's
            # status after the revert.
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The revert undid the clearing write, so the created slot
            # survives.
            worker: Account(storage={SLOT_CREATED: 1}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


BLOCK_GAS_LIMIT = 1_000_000
"""
Gas limit of every block, and of the genesis block before them. Its
base fee target, half of it, lies between the execution gas and the
state gas of the state-dominant block, so the two move the next base
fee in opposite directions. It also leaves room for a refunding
transaction and a reserving one with a non-empty frame budget behind
it.
"""


def test_state_reservation_after_refilled_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reserve a second transaction's state gas against the first's net
    state gas, after a cross-frame refill.

    EIP-8141 "Block-level gas accounting": "`block_state_gas_used +=
    tx_state_gas`", where "`tx_state_gas = sum(fr.gas_used.state for fr
    in frame_receipts)`" counts state gas after refills ("the state
    dimension stays net"), and a frame transaction is included only if
    "`state_reservation <= block_gas_limit -
    block_output.block_state_gas_used`".

    The first transaction creates a slot in one frame and clears it in
    the next, so its net state gas is zero although it was charged one
    storage write. The second reserves the block's whole gas limit in
    state gas and is included; a client counting the charge before the
    refill rejects it and the block. The same reservation after a first
    transaction that keeps its state gas is in
    `test_admission_validity.py::test_second_transaction_reservation`.
    """
    sender = pre.fund_eoa()
    # The worker writes its frame's data word into `SLOT_CREATED`.
    create_code = (
        Op.SSTORE(
            SLOT_CREATED,
            Op.CALLDATALOAD(0),
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        + Op.STOP
    )
    worker = pre.deploy_contract(code=create_code)
    first = FrameTransaction.build(
        fork=fork,
        sender=sender,
        settle=False,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=create_code,
                data=(1).to_bytes(32, "big"),
                state_gas_limit=create_code.state_cost(fork),
                state_gas_used=0,
            ),
            default_frame(
                target=worker,
                code=Op.SSTORE(
                    SLOT_CREATED,
                    Op.CALLDATALOAD(0),
                    key_warm=True,
                    original_value=0,
                    current_value=1,
                    new_value=0,
                )
                + Op.STOP,
                data=(0).to_bytes(32, "big"),
                warm=True,
                state_gas_limit=0,
            ),
        ],
    )
    assert first.state_gas == 0

    second = reserving_frame_tx(pre, fork, state_reservation=BLOCK_GAS_LIMIT)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[first, second], gas_limit=BLOCK_GAS_LIMIT)],
        post={
            sender: Account(nonce=1),
            worker: Account(storage={}),
            second.sender: Account(nonce=2),
        },
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )


def refunding_frame_transaction(
    pre: Alloc, fork: Fork
) -> tuple[FrameTransaction, Address]:
    """
    Return a frame transaction clearing four slots, whose refund applies
    capped, and the worker whose slots it clears.
    """
    sender = pre.fund_eoa()
    code = sum((clear(slot) for slot in CLEARED_SLOTS), Bytecode()) + Op.STOP
    worker = pre.deploy_contract(code=code, storage=CLEARED_STORAGE)
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=code.refund(fork),
        frames=[
            verify_frame(),
            default_frame(
                target=worker, code=code, gas_limit_delta=0, state_gas_limit=0
            ),
        ],
    )
    assert tx.effective_refund > 0 and not tx.floor_binds()
    return tx, worker


@pytest.mark.parametrize(
    "excess",
    [
        pytest.param(0, id="fits_pre_refund_capacity"),
        pytest.param(
            1,
            id="exceeds_pre_refund_capacity",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_next_transaction_capacity_after_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    excess: int,
) -> None:
    """
    Reserve a second transaction's execution against the block
    execution gas the first counted before its refund.

    EIP-8141 "Block-level gas accounting": "`block_execution_gas =
    max(gas_used_before_refund - tx_state_gas, calldata_floor_gas)`"
    is added to `block_execution_gas_used`, "the refund lowers the
    payer's cost without freeing the block capacity the transaction
    occupied", and a frame transaction is included only if
    "`execution_reservation <= block_gas_limit -
    block_output.block_execution_gas_used`".

    The first transaction clears four slots and earns a refund. The
    second reserves exactly what the block has left after the first's
    pre-refund execution, or one gas more. A client subtracting the
    first's post-refund gas admits the second in both cases. The same
    reservation after a first transaction without a refund is in
    `test_admission_validity.py::test_second_transaction_reservation`.
    """
    first, worker = refunding_frame_transaction(pre, fork)
    first_block_gas = first.block_gas_used()
    assert first_block_gas > first.payer_gas_used()

    second = reserving_frame_tx(
        pre,
        fork,
        execution_reservation=BLOCK_GAS_LIMIT - first_block_gas + excess,
        error=reservation_error(excess),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            reservation_block(
                [first, second], gas_limit=BLOCK_GAS_LIMIT, excess=excess
            )
        ],
        post={
            first.sender: Account(nonce=0 if excess else 1),
            worker: Account(
                storage=dict.fromkeys(CLEARED_SLOTS, 1 if excess else 0)
            ),
            second.sender: Account(nonce=1 if excess else 2),
        },
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )


def test_cumulative_gas_after_legacy_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Accumulate a refunding frame transaction's post-refund gas onto the
    gas of the transaction before it, and count its pre-refund
    execution toward the block.

    EIP-8141 "Receipt": "`cumulative_gas_used` is still computed by
    adding the total gas used by the transaction with the previous
    cumulative sum", and "Transaction settlement" makes a frame
    transaction's gas used the post-refund `tx_execution_gas +
    tx_state_gas`; "Block-level gas accounting": the block counts
    "`block_execution_gas + tx_state_gas` (execution pre-refund)", and
    the header follows EIP-8037, whose `gas_used` is the larger of the
    two block dimensions.

    A legacy (type-0) transaction runs first; the frame transaction
    after it clears four slots and creates one, next to two padding
    frames that make the block's execution the larger dimension, before
    and after the refund. Its receipt reports the first transaction's
    gas plus its own post-refund gas, and the header the first
    transaction's gas plus the frame transaction's pre-refund
    execution, which excludes its state gas. A client counting the
    frame transaction's post-refund execution toward the block reports
    a header lower by the applied refund.
    """
    first_sender = pre.fund_eoa()
    stop = pre.deploy_contract(code=Op.STOP)
    first_gas = fork.transaction_intrinsic_cost_calculator()()
    # The auto-filled gas limit leaves slack above the gas the call to
    # `STOP` uses, so the receipt cannot report the limit instead.
    first = Transaction(
        sender=first_sender,
        to=stop,
        expected_receipt=TransactionReceipt(cumulative_gas_used=first_gas),
    )

    sender = pre.fund_eoa()
    code = (
        sum((clear(slot) for slot in CLEARED_SLOTS), Bytecode())
        + Op.SSTORE(FRESH_SLOT_BASE, 1)
        + Op.STOP
    )
    state_gas = code.state_cost(fork)
    worker = pre.deploy_contract(code=code, storage=CLEARED_STORAGE)
    second = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=code.refund(fork),
        frames=[
            verify_frame(),
            sender_padding_frame(pre, sender),
            sender_padding_frame(pre, sender),
            default_frame(
                target=worker,
                code=code,
                state_gas_limit=state_gas,
            ),
        ],
    )
    assert second.expected_receipt is not None
    second.expected_receipt.cumulative_gas_used = HexNumber(
        first_gas + second.payer_gas_used()
    )
    block_execution = first_gas + (second.gas_before_refund - second.state_gas)
    # The premises: a refund applies and the slot's state gas is
    # charged, the floor does not set the block's execution, and the
    # execution, before and after the refund, exceeds the state gas, so
    # the header reports it.
    assert second.effective_refund > 0 and second.state_gas == state_gas
    assert not second.floor_binds(after_refund=False)
    assert block_execution - second.effective_refund > state_gas

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[first, second],
                header_verify=Header(gas_used=block_execution),
            )
        ],
        post={
            sender: Account(nonce=1),
            worker: Account(storage={FRESH_SLOT_BASE: 1}),
        },
    )


CREATED_SLOTS = 3
"""Slots each transaction of the state-dominant block creates."""


def test_state_dominant_block_gas_and_base_fee(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Report a block's state gas as its `gas_used` when it exceeds the
    block's execution gas, and update the next base fee from it.

    EIP-8141 "Block-level gas accounting": "Blocks account for the two
    dimensions separately, per EIP-8037" and "The block header
    `gas_used`, the block validity condition, and the base fee update
    rule follow EIP-8037 unchanged"; EIP-8037 sets the header's
    `gas_used` to the larger of the block's execution and state gas.

    Two frame transactions each create three slots with little
    execution, so the block's state gas is six storage writes and
    exceeds both its execution gas and half the block's gas limit. The
    header reports the state gas, and the next block's base fee rises
    from it, where a client reporting the execution gas would lower it.
    """
    code = sum(
        (Op.SSTORE(slot, 1) for slot in range(CREATED_SLOTS)), Bytecode()
    )
    code += Op.STOP
    transactions = []
    for _ in range(2):
        sender = pre.fund_eoa()
        worker = pre.deploy_contract(code=code)
        transactions.append(
            FrameTransaction.build(
                fork=fork,
                sender=sender,
                frames=[
                    verify_frame(state_gas_limit=0),
                    default_frame(
                        target=worker,
                        code=code,
                        state_gas_limit_delta=0,
                    ),
                ],
            )
        )
    first, second = transactions
    assert second.expected_receipt is not None
    second.expected_receipt.cumulative_gas_used = HexNumber(
        first.payer_gas_used() + second.payer_gas_used()
    )
    block_state_gas = sum(tx.state_gas for tx in transactions)
    block_execution_gas = sum(
        tx.block_gas_used() - tx.state_gas for tx in transactions
    )
    # The premise: state dominates, above the base fee target.
    target = BLOCK_GAS_LIMIT // fork.base_fee_elasticity_multiplier()
    assert block_state_gas > max(block_execution_gas, target)

    # A base fee the genesis block states, from which the first block's
    # follows; large enough that the update moves it by more than the
    # one wei minimum increase.
    genesis_base_fee = 1_000
    calculate_base_fee = fork.base_fee_per_gas_calculator()
    first_base_fee = calculate_base_fee(
        parent_base_fee_per_gas=genesis_base_fee,
        parent_gas_used=0,
        parent_gas_limit=BLOCK_GAS_LIMIT,
    )
    next_base_fee = calculate_base_fee(
        parent_base_fee_per_gas=first_base_fee,
        parent_gas_used=block_state_gas,
        parent_gas_limit=BLOCK_GAS_LIMIT,
    )
    execution_only_base_fee = calculate_base_fee(
        parent_base_fee_per_gas=first_base_fee,
        parent_gas_used=block_execution_gas,
        parent_gas_limit=BLOCK_GAS_LIMIT,
    )
    # The premise: the state gas raises the base fee by more than the
    # minimum increase, and the execution gas alone would lower it.
    assert next_base_fee > first_base_fee + 1
    assert execution_only_base_fee < first_base_fee

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=transactions,
                gas_limit=BLOCK_GAS_LIMIT,
                header_verify=Header(gas_used=block_state_gas),
            ),
            Block(
                gas_limit=BLOCK_GAS_LIMIT,
                header_verify=Header(base_fee_per_gas=next_base_fee),
            ),
        ],
        post={tx.sender: Account(nonce=1) for tx in transactions},
        genesis_environment=Environment(
            gas_limit=BLOCK_GAS_LIMIT, base_fee_per_gas=genesis_base_fee
        ),
    )
