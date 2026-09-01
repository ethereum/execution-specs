"""
Transaction gas settlement across a refill rollback for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

An `SSTORE` returning a slot to its transaction-start value refills the
state charge to the frame that created it, lowering that frame's
receipt. When the refilling frame is later rolled back — as a member of
an atomic batch that unrolls, or by reverting itself — the rollback
restores the creating frame's attribution together with the state.

These tests pin both halves of that restore at settlement: the per-frame
state gas each receipt reports, and the transaction's total spent gas.
The spent gas is the intrinsic execution cost plus every frame's final
receipt usage in both dimensions, so a restored refill lands in the
transaction total, not only in the per-frame receipt.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Conditional,
    Fork,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import default_code_frame_gas, default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CREATED = 0x01
"""Slot created in the earlier frame and returned to its start value later."""

SLOT_OWNER_USED = 0x06
"""Probe slot recording the creating frame's restored state gas attribution."""

SLOT_STATUS = 0x08
"""
Probe slot recording the rolled-back frame's receipt status, plus one so
the expected `FAILURE` readback is distinguishable from a slot never
written.
"""

WORKER_FRAME_GAS = 100_000
"""Execution gas budget of the frames running the worker contracts."""


def _spent_gas(fork: Fork, tx: Transaction, receipts: list) -> int:
    """
    Return the transaction's spent gas from its final frame receipts.

    The settlement charges the intrinsic execution cost plus each frame's
    receipt usage in both dimensions. Neither test accrues a surviving
    storage refund: the only slot returned to its start value is undone by
    the rollback under test, so no refund reaches settlement and the spent
    gas is exactly this sum.
    """
    assert tx.frames is not None and tx.signatures is not None
    intrinsic_execution = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        return_cost_deducted_prior_execution=True,
    )
    return (
        intrinsic_execution
        + sum(receipt.gas_used for receipt in receipts)
        + sum(receipt.state_gas_used for receipt in receipts)
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

    # The creating frame reaches the worker cold; the refilling frame that
    # follows it finds the worker warm, the creating frame's success having
    # seeded the transaction's warm address set with it.
    entry_cold = fork.frame_entry_gas_calculator()()
    entry_warm = fork.frame_entry_gas_calculator()(target_warm=True)
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

    verify_exec = default_code_frame_gas(fork, target_warm=True)
    create_exec = entry_cold + create_body.execution_cost(fork)
    refill_exec = entry_warm + refill_body.execution_cost(fork)
    revert_exec = entry_cold + reverter_code.execution_cost(fork)
    probe_exec = entry_cold + probe_code.execution_cost(fork)
    probe_state = 2 * fresh_write_state_cost

    receipts = [
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=verify_exec,
            state_gas_used=0,
        ),
        # The creating frame keeps its full attribution: the unroll undid
        # the refill the batch frame applied to this receipt.
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=create_exec,
            state_gas_used=fresh_write_state_cost,
        ),
        # The batch frames' receipts are re-appended with their state gas
        # zeroed; their execution gas stays charged.
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=refill_exec,
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec.STATUS_FAILURE,
            gas_used=revert_exec,
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=probe_exec,
            state_gas_used=probe_state,
        ),
    ]

    tx = Transaction(
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1).
            default_frame(
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
                data=(1).to_bytes(32, "big"),
            ),
            # Frame 2: open the batch and return the slot to its start
            # value (1 -> 0), refilling frame 1's receipt.
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
            ),
            # Frame 3: terminate the batch with a revert, unrolling it.
            default_frame(target=reverter, gas_limit=WORKER_FRAME_GAS),
            # Frame 4: read frame 1's restored attribution and frame 3's
            # status after the unroll.
            default_frame(target=probe, gas_limit=WORKER_FRAME_GAS),
        ],
    )
    tx.sign()
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=_spent_gas(fork, tx, receipts),
        frame_receipts=receipts,
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

    # The creating frame reaches the worker cold; the refilling frame that
    # follows it finds the worker warm, the creating frame's success having
    # seeded the transaction's warm address set with it.
    entry_cold = fork.frame_entry_gas_calculator()()
    entry_warm = fork.frame_entry_gas_calculator()(target_warm=True)
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
    ).execution_cost(fork)
    refill_store = Op.SSTORE(
        SLOT_CREATED,
        Op.CALLDATALOAD(0),
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    ).execution_cost(fork)

    verify_exec = default_code_frame_gas(fork, target_warm=True)
    # The creating frame stores, evaluates the branch, and falls through
    # to the trailing stop.
    create_exec = entry_cold + create_store + branch_control
    # The refilling frame stores, evaluates the branch, and takes it into
    # the revert.
    refill_exec = entry_warm + refill_store + branch_control + revert_tail
    probe_exec = entry_cold + probe_code.execution_cost(fork)
    probe_state = 2 * fresh_write_state_cost

    receipts = [
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=verify_exec,
            state_gas_used=0,
        ),
        # The revert restored the refill the failing frame applied to this
        # receipt.
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=create_exec,
            state_gas_used=fresh_write_state_cost,
        ),
        FrameReceipt(
            status=Spec.STATUS_FAILURE,
            gas_used=refill_exec,
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=probe_exec,
            state_gas_used=probe_state,
        ),
    ]

    tx = Transaction(
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1).
            default_frame(
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
                data=(1).to_bytes(32, "big"),
            ),
            # Frame 2: return the slot to its start value (1 -> 0),
            # refilling frame 1's receipt, then revert.
            default_frame(target=worker, gas_limit=WORKER_FRAME_GAS),
            # Frame 3: read frame 1's restored attribution and frame 2's
            # status after the revert.
            default_frame(target=probe, gas_limit=WORKER_FRAME_GAS),
        ],
    )
    tx.sign()
    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=_spent_gas(fork, tx, receipts),
        frame_receipts=receipts,
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
