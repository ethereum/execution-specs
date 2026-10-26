"""
Storage refund edge cases for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Storage refunds accumulate across frames into one signed,
transaction-scoped counter; a failed frame's changes to it are
discarded. At settlement the refund is capped at a fifth of the gas
used before refunds, a base that counts both dimensions, while a
state-gas refill has already left the receipts and no cap touches it.
The block counts the execution dimension before the refund, so a
refund lowers what the payer pays without freeing block capacity.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)
from execution_testing.base_types import HexNumber, StorageRootType

from .helpers import (
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

CLEARED_SLOTS = (1, 2, 3, 4)
"""Pre-existing slots holding one, each cleared for a clearing refund."""

CLEARED_STORAGE: StorageRootType = dict.fromkeys(CLEARED_SLOTS, 1)
"""Pre-state storage of a worker clearing `CLEARED_SLOTS`."""

FRESH_SLOT_BASE = 0x100
"""First of the fresh slots a frame creates next to its clears."""

SLOT = 0x01
"""The slot a worker writes with whatever word its frame passes."""

PADDING_READS = 400
"""
Warm balance reads padding a transaction, so a fifth of its gas covers
the refunds the test expects to apply in full.
"""

BLOCK_GAS_LIMIT = 1_000_000
"""Gas limit of the block, and of the genesis block before it."""


def clearing_refund(fork: Fork) -> int:
    """
    Return EIP-8038's `STORAGE_CLEAR_REFUND`: "added if the original
    value is non-zero, the current value is non-zero and the new value
    is zero", and subtracted when such a cleared slot is set non-zero
    again.
    """
    return fork.gas_costs().REFUND_STORAGE_CLEAR


def restoring_refund(fork: Fork) -> int:
    """
    Return EIP-8038's `STORAGE_WRITE`, "refunded if the new value equals
    the original value and differs from the current value": the write
    charge of a cold write less its cold access.
    """
    gas_costs = fork.gas_costs()
    return gas_costs.COLD_STORAGE_WRITE - gas_costs.COLD_STORAGE_ACCESS


def storage_set_cost(fork: Fork) -> int:
    """Return the state gas of one fresh storage write."""
    return Op.SSTORE(0, 1).state_cost(fork)


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
    Return the worker's write of its frame's data word into `SLOT`,
    priced for the given values.
    """
    return Op.SSTORE(
        SLOT,
        Op.CALLDATALOAD(0),
        key_warm=key_warm,
        original_value=original,
        current_value=current,
        new_value=new,
    )


def word(value: int) -> bytes:
    """Return `value` as the 32-byte data word a worker writes."""
    return value.to_bytes(32, "big")


def padding_frame(pre: Alloc, sender: Address) -> FrameCase:
    """
    Return a frame spending execution gas on warm reads of the sender,
    which seeds the warm set, and nothing else.
    """
    code = (
        Op.POP(Op.BALANCE(address=sender, address_warm=True)) * PADDING_READS
        + Op.STOP
    )
    return default_frame(
        target=pre.deploy_contract(code=code),
        code=code,
        gas_limit_delta=0,
        state_gas_limit=0,
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
    storage_set = storage_set_cost(fork)
    code = sum((clear(slot) for slot in CLEARED_SLOTS), Bytecode())
    for index in range(fresh_slots):
        code += Op.SSTORE(FRESH_SLOT_BASE + index, 1)
    refund = len(CLEARED_SLOTS) * clearing_refund(fork)
    if refilled:
        code += Op.SSTORE(
            FRESH_SLOT_BASE,
            0,
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )
        refund += restoring_refund(fork)
    code += Op.STOP
    worker = pre.deploy_contract(code=code, storage=CLEARED_STORAGE)
    state_gas = 0 if refilled else fresh_slots * storage_set

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=code,
                state_gas_limit=fresh_slots * storage_set,
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
    worker_code = Op.SSTORE(SLOT, Op.CALLDATALOAD(0)) + Op.STOP
    worker = pre.deploy_contract(code=worker_code, storage={SLOT: 1})
    reverts = second_outcome is Outcome.REVERT
    second_write_code = worker_write(
        key_warm=True, original=1, current=0, new=second_write
    )
    if reverts:
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
        second_gas = wrapper_code.execution_cost(
            fork
        ) + second_write_code.execution_cost(fork)
        refund = clearing_refund(fork)
        final_value = 0
    else:
        second_target = worker
        second_gas = second_write_code.execution_cost(fork)
        refund = 0
        if second_write == 1:
            refund = restoring_refund(fork)
        final_value = second_write

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            padding_frame(pre, sender),
            # Frame 2: clear the slot (1 -> 0).
            default_frame(
                target=worker,
                code=worker_write(
                    key_warm=False, original=1, current=1, new=0
                ),
                data=word(0),
                state_gas_limit=0,
            ),
            # Frame 3: write it again (0 -> `second_write`); frame 2's
            # success left the worker and its slot warm.
            default_frame(
                target=second_target,
                execution_gas=second_gas,
                data=word(second_write),
                warm=not reverts,
                state_gas_limit=0,
                outcome=second_outcome,
            ),
        ],
    )
    # The premise: the cap never binds.
    assert tx.effective_refund == refund
    assert clearing_refund(fork) <= tx.gas_before_refund // 5

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT: final_value}),
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
    client keeping the refund charges less.
    """
    sender = pre.fund_eoa()
    ending = Op.REVERT(0, 0) if outcome is Outcome.REVERT else Op.INVALID
    code = clear(SLOT) + ending
    worker = pre.deploy_contract(code=code, storage={SLOT: 1})

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            padding_frame(pre, sender),
            default_frame(
                target=worker,
                code=code,
                state_gas_limit=0,
                outcome=outcome,
            ),
        ],
    )
    # The premise: the cap would let the refund apply in full.
    assert clearing_refund(fork) <= tx.gas_before_refund // 5

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), worker: Account(storage={SLOT: 1})},
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
    worker_code = Op.SSTORE(Op.CALLDATALOAD(0), 0) + Op.STOP
    worker = pre.deploy_contract(code=worker_code, storage={1: 1, 2: 1})
    clear_code = Op.SSTORE(
        Op.CALLDATALOAD(0),
        0,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )
    refund = 2 * clearing_refund(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            padding_frame(pre, sender),
            padding_frame(pre, sender),
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

    Frame 1 creates a slot; frame 2 clears it, refilling frame 1's
    receipt to zero state gas and earning the restoring refund. The
    transaction settles with no state gas and the whole restoring
    refund. A client routing the refill through the refund counter
    instead counts the slot's state gas before the refund and caps the
    sum at a fifth of the execution, charging tens of thousands of gas
    more.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT, Op.CALLDATALOAD(0)) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    storage_set = storage_set_cost(fork)
    refund = restoring_refund(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=refund,
        frames=[
            verify_frame(),
            padding_frame(pre, sender),
            # Frame 2: create the slot (0 -> 1); frame 3 refills it.
            default_frame(
                target=worker,
                code=worker_write(
                    key_warm=False, original=0, current=0, new=1
                ),
                data=word(1),
                state_gas_limit=storage_set,
                state_gas_used=0,
            ),
            # Frame 3: clear it (1 -> 0), refilling frame 2's receipt.
            default_frame(
                target=worker,
                code=worker_write(key_warm=True, original=0, current=1, new=0),
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
    assert refund + storage_set > tx.gas_before_refund // 5

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), worker: Account(storage={})},
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
        refund=len(CLEARED_SLOTS) * clearing_refund(fork),
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
    first's post-refund gas admits the second in both cases.
    """
    first, worker = refunding_frame_transaction(pre, fork)
    first_block_gas = first.block_gas_used()
    assert first_block_gas > first.payer_gas_used()

    # A contract sender carries no signature entries and its frame no
    # data, so a frame count prices the intrinsic cost exactly.
    second_sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=1, return_cost_deducted_prior_execution=True
    )
    second = Transaction(
        sender=second_sender,
        nonce=1,
        frames=[
            verify_frame(
                gas_limit=BLOCK_GAS_LIMIT
                - first_block_gas
                - intrinsic
                + excess,
                state_gas_limit=0,
            )
        ],
        error=(
            TransactionException.GAS_ALLOWANCE_EXCEEDED if excess else None
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[first, second],
                gas_limit=BLOCK_GAS_LIMIT,
                exception=(
                    [
                        BlockException.GAS_USED_OVERFLOW,
                        TransactionException.GAS_ALLOWANCE_EXCEEDED,
                    ]
                    if excess
                    else None
                ),
            )
        ],
        post={
            first.sender: Account(nonce=0 if excess else 1),
            worker: Account(
                storage=dict.fromkeys(CLEARED_SLOTS, 1 if excess else 0)
            ),
            second_sender: Account(nonce=1 if excess else 2),
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

    A type-2 transaction runs first; the frame transaction after it
    clears four slots and creates one. Its receipt reports the first
    transaction's gas plus its own post-refund gas, and the header the
    larger of the block's pre-refund execution and its state gas.
    """
    first_sender = pre.fund_eoa()
    stop = pre.deploy_contract(code=Op.STOP)
    first_gas = fork.transaction_intrinsic_cost_calculator()()
    first = Transaction(
        sender=first_sender,
        to=stop,
        gas_limit=first_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=first_gas),
    )

    sender = pre.fund_eoa()
    storage_set = storage_set_cost(fork)
    code = (
        sum((clear(slot) for slot in CLEARED_SLOTS), Bytecode())
        + Op.SSTORE(FRESH_SLOT_BASE, 1)
        + Op.STOP
    )
    worker = pre.deploy_contract(code=code, storage=CLEARED_STORAGE)
    second = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=len(CLEARED_SLOTS) * clearing_refund(fork),
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=code,
                state_gas_limit=storage_set,
            ),
        ],
    )
    assert second.expected_receipt is not None
    assert second.effective_refund > 0 and second.state_gas == storage_set
    second.expected_receipt.cumulative_gas_used = HexNumber(
        first_gas + second.payer_gas_used()
    )
    block_execution = first_gas + second.block_gas_used() - storage_set

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[first, second],
                header_verify=Header(
                    gas_used=max(block_execution, storage_set)
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            worker: Account(storage={FRESH_SLOT_BASE: 1}),
        },
    )
