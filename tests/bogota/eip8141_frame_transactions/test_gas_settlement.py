"""
Transaction-level gas settlement tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction's payer-facing `gas_used` is the post-refund execution
usage held to the EIP-7976 calldata floor plus final attributed state gas.
Block accounting keeps the same state dimension but counts execution before
storage refunds, as required by EIP-7778.

A storage refill that a frame rollback returns to its owner — by an
atomic batch unroll or by the refilling frame's own revert — lands back
in the spent gas, not only in the restored per-frame receipt. The
state-dimension halves of those rollback scenarios are pinned in
`test_state_gas.py`.
"""

from typing import List, Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Frame,
    FrameReceipt,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import (
    default_code_frame_gas,
    default_frame,
    floor_binding_padding,
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

WORKER_FRAME_GAS = 100_000
"""Execution gas budget of the frames running the worker contracts."""


def _spent_gas(fork: Fork, tx: Transaction, receipts: list) -> int:
    """
    Return the transaction's spent gas before the refund and the floor.

    The settlement charges the intrinsic execution cost plus each
    frame's final receipt usage in both dimensions. A caller whose
    transaction accrues a surviving refund subtracts it, and one whose
    calldata floor may bind clamps the result to the floor; with
    neither in play the sum is the spent gas.
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
def test_calldata_floor_with_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    with_state_write: bool,
    floor_bound: bool,
) -> None:
    """
    Bind the calldata floor on a transaction that also grows state.

    The floor is compared against the execution dimension alone, so a
    floor-bound transaction pays the floor plus its state gas in full:
    state growth never rides free under the data floor. The frame data
    is the fewest bytes that bind the floor, or one byte less in
    `below_floor`, where the execution dimension binds again.
    """
    approve = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
    # A contract sender carries no signature entries, so the charged data
    # is the frame data alone and the floor starts below the standard cost.
    sender = pre.deploy_contract(code=approve, balance=10**18)
    write = Op.SSTORE(
        SLOT_CREATED, 1, key_warm=False, original_value=0, new_value=1
    )
    worker_code = (write if with_state_write else Bytecode()) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    state_used = worker_code.state_cost(fork)
    # Every frame budget is exactly what its execution uses, so the
    # execution dimension is known to the byte.
    entry_gas = fork.frame_entry_gas_calculator()
    verify_gas = entry_gas(target_warm=True) + approve.execution_cost(fork)
    worker_gas = entry_gas(target_warm=False) + worker_code.execution_cost(
        fork
    )
    intrinsic_calculator = fork.frame_transaction_intrinsic_cost_calculator()
    floor_calculator = fork.frame_transaction_data_floor_cost_calculator()

    def frames(data_length: int) -> List[Frame]:
        """Return the frames with `data_length` bytes of worker data."""
        return [
            verify_frame(gas_limit=verify_gas, state_gas_limit=0),
            default_frame(
                target=worker,
                gas_limit=worker_gas,
                state_gas_limit=state_used,
                data=bytes(data_length),
            ),
        ]

    def execution_used(data_length: int) -> int:
        return (
            intrinsic_calculator(
                frames=frames(data_length),
                return_cost_deducted_prior_execution=True,
            )
            + verify_gas
            + worker_gas
        )

    def floor_binds(data_length: int) -> bool:
        return floor_calculator(frames=frames(data_length)) > execution_used(
            data_length
        )

    data_length = floor_binding_padding(floor_binds)
    if not floor_bound:
        data_length -= 1
    gas_used = max(
        execution_used(data_length),
        floor_calculator(frames=frames(data_length)),
    )
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames(data_length),
        expected_receipt=TransactionReceipt(
            payer=sender, cumulative_gas_used=gas_used + state_used
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            worker: Account(
                storage={SLOT_CREATED: 1 if with_state_write else 0}
            ),
        },
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
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )
    # Pad execution so the refund cap — a fifth of the pre-refund
    # usage — stays above the clearing refund and the refund applies
    # in full. The sender seeds the warm set, so its repeated balance
    # reads are warm accesses.
    padding = Op.POP(Op.BALANCE(address=sender, address_warm=True)) * 400
    worker_code = padding + clear + Op.STOP
    worker = pre.deploy_contract(code=worker_code, storage={SLOT_CREATED: 1})

    verify_gas = default_code_frame_gas(fork, target_warm=True)
    frame_execution_gas = fork.frame_entry_gas_calculator()() + (
        worker_code.execution_cost(fork)
    )
    receipts = [
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=verify_gas,
            state_gas_used=0,
        ),
        # The receipt reports pre-refund execution gas; the refund
        # applies only at transaction settlement.
        FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=frame_execution_gas,
            state_gas_used=0,
        ),
    ]

    refund = worker_code.refund(fork)

    def build(data_length: int) -> Tuple[Transaction, int, int]:
        """
        Return the signed transaction, its spent gas before the refund
        and its calldata floor.
        """
        tx = Transaction(
            sender=sender,
            nonce=0,
            frames=[
                verify_frame(),
                default_frame(
                    target=worker,
                    gas_limit=WORKER_FRAME_GAS,
                    state_gas_limit=0,
                    data=bytes(data_length),
                ),
            ],
        )
        # Materialize the signature bytes the intrinsic cost and calldata
        # floor charge for.
        tx.sign()
        assert tx.frames is not None and tx.signatures is not None
        calldata_floor = fork.frame_transaction_data_floor_cost_calculator()(
            frames=tx.frames, signatures=tx.signatures
        )
        return tx, _spent_gas(fork, tx, receipts), calldata_floor

    def floor_binds(data_length: int) -> bool:
        _, gas_used_before_refund, calldata_floor = build(data_length)
        if boundary == "post_refund":
            return calldata_floor > gas_used_before_refund - refund
        return calldata_floor > gas_used_before_refund

    data_length = floor_binding_padding(floor_binds)
    if floor_side == "below":
        data_length -= 1
    tx, gas_used_before_refund, calldata_floor = build(data_length)
    # The premise of the test: the refund applies uncapped.
    assert 0 < refund <= gas_used_before_refund // fork.max_refund_quotient()
    gas_used_after_refund = gas_used_before_refund - refund
    # The premise of each case: the floor sits below the post-refund
    # gas, above the pre-refund gas, or between the two.
    if (boundary, floor_side) == ("post_refund", "below"):
        assert calldata_floor < gas_used_after_refund
    elif (boundary, floor_side) == ("pre_refund", "above"):
        assert gas_used_before_refund < calldata_floor
    else:
        assert gas_used_after_refund < calldata_floor < gas_used_before_refund

    payer_gas_used = max(gas_used_after_refund, calldata_floor)
    block_gas_used = max(gas_used_before_refund, calldata_floor)

    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=payer_gas_used,
        frame_receipts=receipts,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0}),
        },
        blockchain_test_header_verify=Header(gas_used=block_gas_used),
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
    # No refund survives to settlement: the only slot returned to its
    # start value is undone by the rollback under test.
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
    # No refund survives to settlement: the only slot returned to its
    # start value is undone by the rollback under test.
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
