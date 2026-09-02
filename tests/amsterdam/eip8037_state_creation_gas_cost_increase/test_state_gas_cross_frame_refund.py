"""
Test where a state gas refund lands when it is credited in a
different frame than the spilled charge it undoes.

A state charge spilled from `gas_left` can be refunded in a child
frame. The credit lands in the child's reservoir and merges upward as
reservoir, so `gas_left` is never repaid mid-transaction. The parked
credit still funds later state creation at full price and returns to
the sender at settlement, so cross-frame placement opens no discount
on state and costs the sender nothing at the transaction boundary.

The merge-time repayment proposed in [ethereum/EIPs#12265]
(https://github.com/ethereum/EIPs/pull/12265) moves the credit back
to `gas_left` when a successful child merges. The placement pins here
flip under it, while the settlement pins are placement-independent
and must hold unchanged.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Fork,
    Op,
    Opcode,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

SLOT_X = 1
SLOT_Y = 2
SLOT_MARKER = 3
SLOT_RESULT = 4
SLOT_INCREASED = 5


def window_cost_excess(result_sstore: Opcode = Op.SSTORE) -> Bytecode:
    """
    Return code storing the first window's cost over the second's.

    Memory holds `g0`, `g1` and `g2` at 0, 32 and 64. The stored
    value is `(g0 - g1) - (g1 - g2)`, the first window's cost minus
    the second's, computed modulo 2**256. `result_sstore` lets
    gas-settlement tests carry metadata on the storing opcode.
    """
    return result_sstore(
        SLOT_RESULT,
        Op.SUB(
            Op.ADD(Op.MLOAD(0), Op.MLOAD(64)),
            Op.ADD(Op.MLOAD(32), Op.MLOAD(32)),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_parks_in_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a cross-frame refund credits the reservoir, not `gas_left`.

    The frame sets a slot with the reservoir empty, spilling the state
    charge from `gas_left`. A delegated child clears the slot and the
    credit lands in the reservoir, where it stays through the merge:
    `gas_left` is lower after the clearing call than before it, and
    the clearing window costs the same as a no-op window.
    """
    clearer = pre.deploy_contract(code=Op.SSTORE(SLOT_X, 0))

    call_window = Op.POP(Op.DELEGATECALL(address=clearer))
    code = (
        # Warm the clearer and the slot while it is still zero, and
        # pre-expand the measurement memory, so the two measured
        # windows below are byte-identical and cost-identical.
        call_window
        + Op.MSTORE(64, 0)
        + Op.SSTORE(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        + call_window
        + Op.MSTORE(32, Op.GAS)
        + call_window
        + Op.MSTORE(64, Op.GAS)
        + Op.SSTORE(SLOT_INCREASED, Op.GT(Op.MLOAD(32), Op.MLOAD(0)))
        + window_cost_excess()
        # Every other expected slot is zero, so the marker is what
        # distinguishes the pinned run from a reverted one.
        + Op.SSTORE(SLOT_MARKER, 1)
    )
    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    # Under the merge-time repayment of ethereum/EIPs#12265 the
    # clearing window repays the spill: the increase flag becomes 1
    # and the window excess wraps to minus the slot's state cost.
    post = {
        contract: Account(
            storage={
                SLOT_X: 0,
                SLOT_MARKER: 1,
                SLOT_INCREASED: 0,
                SLOT_RESULT: 0,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_parked_credit_returns_at_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the parked credit refunds the sender at settlement.

    The frame's spilled set is cleared by a child, parking the credit
    in the reservoir. Settlement sums `gas_left` and the reservoir, so
    the spilled charge and the parked credit cancel and the receipt
    carries no state term at all. The receipt is placement-independent
    and holds unchanged under ethereum/EIPs#12265.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    clearer_code = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)

    # A budget covering the child's SSTORE stipend sentry through the
    # clear, so the child succeeds and returns the sentry unspent.
    child_budget = (
        fork.call_value_stipend() + 1 + clearer_code.execution_cost(fork)
    )
    code = Op.SSTORE(
        SLOT_X,
        1,
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    ) + Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=clearer, address_warm=False)
    )
    contract = pre.deploy_contract(code=code)

    before_refund = (
        intrinsic_cost
        + code.execution_cost(fork)
        + clearer_code.execution_cost(fork)
    )
    # Clearing the slot back to its original value also refunds the
    # write cost through the classic refund counter at settlement.
    restore_refund = clearer_code.refund(fork) - sstore_state_gas
    expected_gas_used = before_refund - min(
        before_refund // fork.max_refund_quotient(), restore_refund
    )
    # The post-refund usage must clear the calldata floor, or the
    # floor masks a lost or doubled credit.
    assert expected_gas_used > fork.transaction_data_floor_cost_calculator()(
        data=b""
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    post = {contract: Account(storage={SLOT_X: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_parked_credit_funds_state_at_full_price(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the parked credit funds a later creation at full price.

    After the cross-frame clear parks the credit, a fresh set draws
    its state charge from the reservoir: `gas_left` drops by only the
    execution premium across the set window. The receipt still bills
    both surviving slots at the full state price, so routing a refund
    through another frame buys no discount on state that persists.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    clearer_code = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)
    child_budget = (
        fork.call_value_stipend() + 1 + clearer_code.execution_cost(fork)
    )

    fresh_set = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    window_1 = fresh_set(SLOT_Y, 1)
    window_2 = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=1,
    )(SLOT_Y, 1)
    # The windows are byte-identical, so the excess is the fresh set's
    # execution premium plus whatever its state charge takes from
    # `gas_left`. The parked credit covers the state charge, leaving
    # the execution premium alone. Under ethereum/EIPs#12265 the merge
    # drains the credit into `gas_left` first, so the set spills and
    # the excess grows by the slot's state cost.
    execution_premium = window_1.execution_cost(
        fork
    ) - window_2.execution_cost(fork)

    code = (
        Op.MSTORE(64, 0, new_memory_size=96, old_memory_size=0)
        + fresh_set(SLOT_X, 1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=child_budget, address=clearer, address_warm=False
            )
        )
        + Op.MSTORE(0, Op.GAS)
        + window_1
        + Op.MSTORE(32, Op.GAS)
        + window_2
        + Op.MSTORE(64, Op.GAS)
        + window_cost_excess(result_sstore=fresh_set)
    )
    contract = pre.deploy_contract(code=code)

    # Slot Y and the result slot survive, each fully priced. The
    # cleared slot cancels out of the settlement sum.
    before_refund = (
        intrinsic_cost
        + code.execution_cost(fork)
        + clearer_code.execution_cost(fork)
        + 2 * sstore_state_gas
    )
    restore_refund = clearer_code.refund(fork) - sstore_state_gas
    expected_gas_used = before_refund - min(
        before_refund // fork.max_refund_quotient(), restore_refund
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    post = {
        contract: Account(
            storage={
                SLOT_X: 0,
                SLOT_Y: 1,
                SLOT_RESULT: execution_premium,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_parked_credit_cannot_fund_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the parked credit cannot fund execution work.

    The gas limit covers the transaction only up to the clearing
    child's merge plus a sliver. An execution tail worth less than the
    parked credit follows, and the transaction halts anyway: the
    credit sits in the reservoir, spendable on state creation alone.
    Under ethereum/EIPs#12265 the merge repays the spill and the same
    budget completes.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    clearer_code = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)

    fresh_set = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    head = (
        fresh_set(SLOT_MARKER, 1)
        + fresh_set(SLOT_X, 1)
        + Op.POP(
            Op.DELEGATECALL(gas=Op.GAS, address=clearer, address_warm=False)
        )
    )
    # TODO: The tail spends a set amount of execution gas; a JUMPDEST
    # run is the most future-proof inline way until a fork util exists.
    tail_ops = min(
        sstore_state_gas // Op.JUMPDEST.gas_cost(fork),
        fork.max_code_size() - len(head),
    )
    tail = Op.JUMPDEST * tail_ops
    code = head + tail
    contract = pre.deploy_contract(code=code)

    # A sliver covering the child's SSTORE stipend sentry through the
    # one-in-64 withholding. It survives the merge unspent.
    sliver = (
        fork.call_value_stipend() + 1 + clearer_code.execution_cost(fork)
    ) * 64 // 63 + 1
    tail_cost = tail.gas_cost(fork)
    # The tail must overrun the sliver yet fit inside the parked
    # credit, or the halt stops demonstrating the credit cannot buy
    # execution.
    assert sliver < tail_cost <= sstore_state_gas

    gas_limit = (
        intrinsic_cost
        + head.gas_cost(fork)
        + clearer_code.gas_cost(fork)
        + sliver
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
    )

    post = {contract: Account(storage={SLOT_MARKER: 0, SLOT_X: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("child_ending", ["stop", "revert", "invalid"])
@pytest.mark.valid_from("EIP8037")
def test_child_clear_repays_own_spill_first(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    child_ending: str,
) -> None:
    """
    Test the cross-slot LIFO split of a cross-frame refund in a child.

    The parent spills two fresh sets; a delegated child spills a set
    of its own, then clears both parent slots. The first credit repays
    the child's borrow, the second parks in the reservoir, and a
    failing child discards the parked credit with its rollback.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    fresh_set = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    warm_clear = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )

    child_body = (
        fresh_set(SLOT_MARKER, 1)
        + warm_clear(SLOT_X, 0)
        + warm_clear(SLOT_Y, 0)
    )
    if child_ending == "stop":
        child_code = child_body + Op.STOP
    elif child_ending == "revert":
        child_code = child_body + Op.REVERT(0, 0)
    elif child_ending == "invalid":
        child_code = child_body + Op.INVALID
    else:
        raise ValueError(f"unhandled child ending: {child_ending}")
    child = pre.deploy_contract(code=child_code)

    # A budget covering the child's SSTORE stipend sentry through its
    # own spilled set and both clears.
    child_budget = fork.call_value_stipend() + 1 + child_code.gas_cost(fork)

    call_window = Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    code = (
        fresh_set(SLOT_X, 1)
        + fresh_set(SLOT_Y, 1)
        + Op.MSTORE(32, 0, new_memory_size=64, old_memory_size=0)
        + Op.MSTORE(0, Op.GAS)
        + call_window
        + Op.MSTORE(32, Op.GAS)
        + fresh_set(SLOT_RESULT, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
    )
    contract = pre.deploy_contract(code=code)

    if child_ending == "stop":
        child_consumed = child_code.execution_cost(fork)
    elif child_ending == "revert":
        child_consumed = child_code.execution_cost(fork)
    elif child_ending == "invalid":
        child_consumed = child_budget
    else:
        raise ValueError(f"unhandled child ending: {child_ending}")
    # Gas measured between the two reads: the first stamp's store, the
    # call window, the child's consumption, and the second read itself.
    window_cost = (
        Op.MSTORE(0, Op.GAS).gas_cost(fork)
        + call_window.execution_cost(fork)
        + child_consumed
    )

    parent_exec = code.execution_cost(fork)
    if child_ending == "stop":
        # The child's slot and the result slot survive; the child's
        # borrow was repaid by the first clear's credit, so only the
        # parked second credit cancels a parent spill at settlement.
        before_refund = (
            intrinsic_cost
            + parent_exec
            + child_code.execution_cost(fork)
            + 2 * sstore_state_gas
        )
        restore_refund = 2 * (warm_clear.refund(fork) - sstore_state_gas)
        expected_gas_used = before_refund - min(
            before_refund // fork.max_refund_quotient(), restore_refund
        )
    elif child_ending == "revert":
        expected_gas_used = (
            intrinsic_cost
            + parent_exec
            + child_code.execution_cost(fork)
            + 3 * sstore_state_gas
        )
    elif child_ending == "invalid":
        expected_gas_used = (
            intrinsic_cost + parent_exec + child_budget + 3 * sstore_state_gas
        )
    else:
        raise ValueError(f"unhandled child ending: {child_ending}")

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    if child_ending == "stop":
        storage = {
            SLOT_X: 0,
            SLOT_Y: 0,
            SLOT_MARKER: 1,
            SLOT_RESULT: window_cost,
        }
    elif child_ending in ("revert", "invalid"):
        storage = {
            SLOT_X: 1,
            SLOT_Y: 1,
            SLOT_MARKER: 0,
            SLOT_RESULT: window_cost,
        }
    else:
        raise ValueError(f"unhandled child ending: {child_ending}")

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_after_delegation_spill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a cross-frame refund after the sender's delegation spilled.

    A set-code transaction with an empty reservoir pays its delegation
    from `gas_left` and commits that spill before the code runs. The
    code spills a fresh set and a delegated child clears it. The call
    costs the same as without the delegation and the delegation stays
    billed.
    """
    fresh_set = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    warm_clear = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )

    child_code = warm_clear(SLOT_X, 0)
    child = pre.deploy_contract(code=child_code)
    # SSTORE needs more than the call stipend left, so give the child
    # that much on top of its cost.
    child_budget = fork.call_value_stipend() + 1 + child_code.gas_cost(fork)

    call = Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    code = (
        Op.MSTORE(32, 0, new_memory_size=64, old_memory_size=0)
        + fresh_set(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        + call
        + Op.MSTORE(32, Op.GAS)
        + fresh_set(SLOT_RESULT, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
    )
    contract = pre.deploy_contract(code=code)

    signer = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
    ]

    # The window runs from one GAS read to the next: the store of the
    # first read, the call and the second read.
    call_cost = (
        Op.MSTORE(0, Op.GAS).gas_cost(fork)
        + call.execution_cost(fork)
        + child_code.execution_cost(fork)
    )

    gas_used = (
        fork.transaction_intrinsic_cost_calculator()(
            authorization_list_or_count=authorization_list,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_gas_calculator()(
            authorizations=authorization_list
        )
        + fork.transaction_top_frame_state_gas(
            authorizations=authorization_list
        )
        + code.gas_cost(fork)
        + child_code.gas_cost(fork)
        - child_code.state_refund(fork)
    )
    refund = child_code.refund(fork) - child_code.state_refund(fork)
    gas_used -= min(gas_used // fork.max_refund_quotient(), refund)

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    post = {
        contract: Account(storage={SLOT_X: 0, SLOT_RESULT: call_cost}),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(pre=pre, post=post, tx=tx)
