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

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Header,
    Op,
    StateTestFiller,
)

from .helpers import (
    FrameTransaction,
    Outcome,
    default_frame,
    floor_binding_padding,
    state_slots,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


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
    (worker_slot,) = state_slots(1)
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
        worker_slot.key, 1, key_warm=False, original_value=0, new_value=1
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
                storage={worker_slot.key: 1 if with_state_write else 0}
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
    (worker_slot,) = state_slots(1)
    clear = Op.SSTORE(
        worker_slot.key,
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
    worker = pre.deploy_contract(
        code=worker_code, storage={worker_slot.key: 1}
    )
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
            worker: Account(storage={worker_slot.key: 0}),
        },
        blockchain_test_header_verify=Header(gas_used=tx.block_gas_used()),
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
    worker_slot, owner_used, status = state_slots(3)
    creation_cost = worker_slot.creation_cost(fork)

    # A passive worker that writes whichever value its frame passes: the
    # creating frame passes one, the refilling frame passes zero.
    worker_code = Op.SSTORE(worker_slot.key, Op.CALLDATALOAD(0)) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)
    reverter_code = Op.REVERT(0, 0)
    reverter = pre.deploy_contract(code=reverter_code)
    probe_code = (
        owner_used.record(1, Spec.FRAMEPARAM_STATE_GAS_USED)
        + status.record(3, Spec.FRAMEPARAM_STATUS)
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    create_body = (
        Op.SSTORE(
            worker_slot.key,
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
            worker_slot.key,
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
            worker: Account(storage={worker_slot.key: 1}),
            probe: Account(
                storage={
                    owner_used.key: owner_used.recorded(creation_cost),
                    status.key: status.recorded(Spec.STATUS_FAILURE),
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
    worker_slot, owner_used, status = state_slots(3)
    creation_cost = worker_slot.creation_cost(fork)

    # A worker that writes whichever value its frame passes and then
    # reverts when called with empty data: the creating frame passes a
    # value word and stops, the refilling frame passes no data and reverts.
    worker_code = Op.SSTORE(worker_slot.key, Op.CALLDATALOAD(0)) + Conditional(
        condition=Op.ISZERO(Op.CALLDATASIZE),
        if_true=Op.REVERT(0, 0),
        if_false=Op.STOP,
    )
    worker = pre.deploy_contract(code=worker_code)
    probe_code = (
        owner_used.record(1, Spec.FRAMEPARAM_STATE_GAS_USED)
        + status.record(2, Spec.FRAMEPARAM_STATUS)
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
        worker_slot.key,
        Op.CALLDATALOAD(0),
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    refill_store = Op.SSTORE(
        worker_slot.key,
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
            worker: Account(storage={worker_slot.key: 1}),
            probe: Account(
                storage={
                    owner_used.key: owner_used.recorded(creation_cost),
                    status.key: status.recorded(Spec.STATUS_FAILURE),
                }
            ),
        },
    )
