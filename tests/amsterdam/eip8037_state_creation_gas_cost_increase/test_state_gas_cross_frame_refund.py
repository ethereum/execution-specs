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
    Address,
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

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

SLOT_X = 1
SLOT_Y = 2
SLOT_MARKER = 3
SLOT_RESULT = 4
SLOT_INCREASED = 5
SLOT_PROBE = 6
SLOT_PROBE_RESULT = 7

# A cold set of a slot that was zero when the transaction began, and
# the warm clear that undoes it.
FRESH_SET = Op.SSTORE.with_metadata(
    key_warm=False, original_value=0, current_value=0, new_value=1
)
WARM_CLEAR = Op.SSTORE.with_metadata(
    key_warm=True, original_value=0, current_value=1, new_value=0
)


def window_cost_excess() -> Bytecode:
    """
    Return code storing the first window's cost over the second's.

    Memory holds `g0`, `g1` and `g2` at 0, 32 and 64. The stored
    value is `(g0 - g1) - (g1 - g2)`, the first window's cost minus
    the second's, computed modulo 2**256.
    """
    return FRESH_SET(
        SLOT_RESULT,
        Op.SUB(
            Op.ADD(Op.MLOAD(0), Op.MLOAD(64)),
            Op.ADD(Op.MLOAD(32), Op.MLOAD(32)),
        ),
    )


def deploy_slot_holder(pre: Alloc) -> Address:
    """
    Deploy the contract owning the slot the dispatches clear.

    It stores its calldata size, so a call carrying one byte sets the
    slot and a call carrying none clears it.
    """
    return pre.deploy_contract(code=Op.SSTORE(SLOT_X, Op.CALLDATASIZE))


def budget_above_sstore_stipend(fork: Fork, code: Bytecode) -> int:
    """
    Return a call budget leaving the child more than the stipend.

    SSTORE refuses to run with only the call stipend left, so a child
    that stores needs that much on top of what its code costs.
    """
    return fork.call_value_stipend() + 1 + code.gas_cost(fork)


def delegation_to(
    pre: Alloc, contract: Address
) -> tuple[Address, list[AuthorizationTuple]]:
    """Return a signer and the authorization delegating it to `contract`."""
    signer = pre.fund_eoa()
    return signer, [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        )
    ]


def clearing_child_code(child_ending: str) -> Bytecode:
    """
    Return child code spilling a set, clearing both parent slots,
    then ending as `child_ending` says.
    """
    body = (
        FRESH_SET(SLOT_MARKER, 1)
        + WARM_CLEAR(SLOT_X, 0)
        + WARM_CLEAR(SLOT_Y, 0)
    )
    if child_ending == "stop":
        return body + Op.STOP
    if child_ending == "revert":
        return body + Op.REVERT(0, 0)
    if child_ending == "invalid":
        return body + Op.INVALID
    raise ValueError(f"unhandled child ending: {child_ending}")


def clearing_child_storage(child_ending: str) -> dict[int, int]:
    """Return the parent storage a child with this ending leaves behind."""
    if child_ending == "stop":
        return {SLOT_X: 0, SLOT_Y: 0, SLOT_MARKER: 1}
    return {SLOT_X: 1, SLOT_Y: 1, SLOT_MARKER: 0}


def clearing_probe_code(
    set_slot: Bytecode, windows: list[Bytecode]
) -> Bytecode:
    """
    Return code measuring a clearing window against a no-op window.

    `windows` holds three copies of the dispatch under test. The first
    warms the target and the slot while the slot is still zero, and
    pre-expands the measurement memory, so the two measured windows
    below are byte-identical and cost-identical. `set_slot` then sets
    the slot with the reservoir empty, spilling the state charge. The
    first measured window clears the slot and the second repeats as a
    no-op, so the refunded state gas is what separates their cost.
    """
    warm, first, second = windows
    return (
        warm
        + Op.MSTORE(64, 0)
        + set_slot
        + Op.MSTORE(0, Op.GAS)
        + first
        + Op.MSTORE(32, Op.GAS)
        + second
        + Op.MSTORE(64, Op.GAS)
        + Op.SSTORE(SLOT_INCREASED, Op.GT(Op.MLOAD(32), Op.MLOAD(0)))
        + window_cost_excess()
        # The marker distinguishes the pinned run from a reverted one.
        + Op.SSTORE(SLOT_MARKER, 1)
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
    window = Op.POP(Op.DELEGATECALL(address=clearer))
    contract = pre.deploy_contract(
        code=clearing_probe_code(Op.SSTORE(SLOT_X, 1), [window] * 3)
    )

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

    clearer_code = WARM_CLEAR(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)

    # A budget covering the child's SSTORE stipend sentry through the
    # clear, so the child succeeds and returns the sentry unspent.
    child_budget = budget_above_sstore_stipend(fork, clearer_code)
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
    Test the sender pays full price for a set the parked refund funded.

    A fresh set spills, a delegated child clears it and the refund
    parks in the reservoir, then a second fresh set draws on it. The
    surviving slot is billed at the full state price, so routing a
    refund through another frame buys no discount on state that
    persists. What the set costs `gas_left` is measured in
    `test_parked_refund_covers_a_later_set`.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    clearer_code = WARM_CLEAR(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)
    child_budget = budget_above_sstore_stipend(fork, clearer_code)

    code = (
        FRESH_SET(SLOT_X, 1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=child_budget, address=clearer, address_warm=False
            )
        )
        + FRESH_SET(SLOT_Y, 1)
    )
    contract = pre.deploy_contract(code=code)

    # Slot Y survives, fully priced. The cleared slot cancels out of
    # the settlement sum.
    before_refund = (
        intrinsic_cost
        + code.execution_cost(fork)
        + clearer_code.execution_cost(fork)
        + sstore_state_gas
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

    post = {contract: Account(storage={SLOT_X: 0, SLOT_Y: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_parked_refund_covers_a_later_set(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a set funded by the parked refund costs `gas_left` nothing.

    After the cross-frame clear parks the refund, a fresh set draws
    its state charge from the reservoir, so `gas_left` drops by only
    the set's execution premium over a warm re-set of the same slot.
    What the sender pays for it is checked in
    `test_parked_credit_funds_state_at_full_price`.
    """
    clearer_code = WARM_CLEAR(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)
    child_budget = budget_above_sstore_stipend(fork, clearer_code)

    window_1 = FRESH_SET(SLOT_Y, 1)
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
        + FRESH_SET(SLOT_X, 1)
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
        + window_cost_excess()
    )
    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
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

    clearer_code = WARM_CLEAR(SLOT_X, 0)
    clearer = pre.deploy_contract(code=clearer_code)

    head = (
        FRESH_SET(SLOT_MARKER, 1)
        + FRESH_SET(SLOT_X, 1)
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
    sliver = budget_above_sstore_stipend(fork, clearer_code) * 64 // 63 + 1
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
    failing child discards the parked refund with its rollback. What
    the call costs `gas_left` is measured in
    `test_child_clear_window_cost`.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = clearing_child_code(child_ending)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    code = (
        FRESH_SET(SLOT_X, 1)
        + FRESH_SET(SLOT_Y, 1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=child_budget, address=child, address_warm=False
            )
        )
    )
    contract = pre.deploy_contract(code=code)

    parent_exec = code.execution_cost(fork)
    if child_ending == "stop":
        # Only the child's own slot survives. Its borrow was repaid by
        # the first clear's refund, so the parked second refund cancels
        # a parent spill at settlement.
        before_refund = (
            intrinsic_cost
            + parent_exec
            + child_code.execution_cost(fork)
            + sstore_state_gas
        )
        restore_refund = 2 * (WARM_CLEAR.refund(fork) - sstore_state_gas)
        expected_gas_used = before_refund - min(
            before_refund // fork.max_refund_quotient(), restore_refund
        )
    elif child_ending == "revert":
        expected_gas_used = (
            intrinsic_cost
            + parent_exec
            + child_code.execution_cost(fork)
            + 2 * sstore_state_gas
        )
    else:
        expected_gas_used = (
            intrinsic_cost + parent_exec + child_budget + 2 * sstore_state_gas
        )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    post = {contract: Account(storage=clearing_child_storage(child_ending))}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("child_ending", ["stop", "revert", "invalid"])
@pytest.mark.valid_from("EIP8037")
def test_child_clear_window_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    child_ending: str,
) -> None:
    """
    Test the clearing call costs `gas_left` its execution and no more.

    The same shape as `test_child_clear_repays_own_spill_first`, with
    the call bracketed by two `GAS` reads. Neither the refund the
    child parks nor the spill it repays reaches `gas_left`, so the
    window costs the call and the child's execution alone. What the
    sender pays is checked there.
    """
    child_code = clearing_child_code(child_ending)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    call_window = Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    code = (
        FRESH_SET(SLOT_X, 1)
        + FRESH_SET(SLOT_Y, 1)
        + Op.MSTORE(32, 0, new_memory_size=64, old_memory_size=0)
        + Op.MSTORE(0, Op.GAS)
        + call_window
        + Op.MSTORE(32, Op.GAS)
        + FRESH_SET(SLOT_RESULT, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
    )
    contract = pre.deploy_contract(code=code)

    # An invalid child burns its whole budget; the others stop at the
    # end of their code.
    child_consumed = (
        child_budget
        if child_ending == "invalid"
        else child_code.execution_cost(fork)
    )
    # Gas measured between the two reads: the first stamp's store, the
    # call window, the child's consumption, and the second read itself.
    window_cost = (
        Op.MSTORE(0, Op.GAS).gas_cost(fork)
        + call_window.execution_cost(fork)
        + child_consumed
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(
            storage={
                **clearing_child_storage(child_ending),
                SLOT_RESULT: window_cost,
            }
        )
    }
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
    code spills a fresh set and a delegated child clears it. The
    delegation stays billed: the refund does not reach the committed
    spill. What the call costs `gas_left` is measured in
    `test_delegation_spill_window_cost`.
    """
    child_code = WARM_CLEAR(SLOT_X, 0)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    code = FRESH_SET(SLOT_X, 1) + Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    contract = pre.deploy_contract(code=code)

    signer, authorization_list = delegation_to(pre, contract)

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
        contract: Account(storage={SLOT_X: 0}),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_delegation_spill_window_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the clearing call costs the same after a delegation spilled.

    The same shape as `test_cross_frame_refund_after_delegation_spill`,
    with the call bracketed by two `GAS` reads. The refund the child
    merges reaches neither `gas_left` nor the committed spill, so the
    window costs the call and the child's execution alone. What the
    sender pays is checked there.
    """
    child_code = WARM_CLEAR(SLOT_X, 0)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    call = Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    code = (
        Op.MSTORE(32, 0, new_memory_size=64, old_memory_size=0)
        + FRESH_SET(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        + call
        + Op.MSTORE(32, Op.GAS)
        + FRESH_SET(SLOT_RESULT, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
    )
    contract = pre.deploy_contract(code=code)

    signer, authorization_list = delegation_to(pre, contract)

    # The window runs from one GAS read to the next: the store of the
    # first read, the call and the second read.
    call_cost = (
        Op.MSTORE(0, Op.GAS).gas_cost(fork)
        + call.execution_cost(fork)
        + child_code.execution_cost(fork)
    )

    tx = Transaction(
        to=contract,
        authorization_list=authorization_list,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage={SLOT_X: 0, SLOT_RESULT: call_cost}),
        signer: Account(code=Spec7702.delegation_designation(contract)),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("reservoir_slots", [0, 1, 2])
@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_with_reservoir_grant(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir_slots: int,
) -> None:
    """
    Test the receipt is the same however much reservoir was bought.

    The reservoir covers none, one or both of the parent's two sets
    and the rest spill. A delegated child clears both slots and a
    later set draws on whatever is left. The receipt is the same in
    every case, so buying reservoir up front costs the sender nothing
    and saves nothing. What the call and the set cost `gas_left` is
    measured in `test_reservoir_grant_window_costs`.
    """
    child_code = WARM_CLEAR(SLOT_X, 0) + WARM_CLEAR(SLOT_Y, 0)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    code = (
        FRESH_SET(SLOT_X, 1)
        + FRESH_SET(SLOT_Y, 1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=child_budget, address=child, address_warm=False
            )
        )
        + FRESH_SET(SLOT_PROBE, 1)
    )
    contract = pre.deploy_contract(code=code)

    gas_used = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.gas_cost(fork)
        + child_code.gas_cost(fork)
        - child_code.state_refund(fork)
    )
    refund = child_code.refund(fork) - child_code.state_refund(fork)
    gas_used -= min(gas_used // fork.max_refund_quotient(), refund)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=(
            reservoir_slots * Op.SSTORE(new_value=1).state_cost(fork)
        ),
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    post = {contract: Account(storage={SLOT_X: 0, SLOT_Y: 0, SLOT_PROBE: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("reservoir_slots", [0, 1, 2])
@pytest.mark.valid_from("EIP8037")
def test_reservoir_grant_window_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir_slots: int,
) -> None:
    """
    Test a reservoir grant changes neither window's cost.

    The same shape as `test_cross_frame_refund_with_reservoir_grant`,
    with the call and a later set each bracketed by `GAS` reads. Both
    windows cost the same however much of the parent's two sets the
    reservoir covered: the refund stays in the reservoir and the spill
    is not repaid. What the sender pays is checked there.
    """
    child_code = WARM_CLEAR(SLOT_X, 0) + WARM_CLEAR(SLOT_Y, 0)
    child = pre.deploy_contract(code=child_code)
    child_budget = budget_above_sstore_stipend(fork, child_code)

    call = Op.POP(
        Op.DELEGATECALL(gas=child_budget, address=child, address_warm=False)
    )
    probe = FRESH_SET(SLOT_PROBE, 1)
    code = (
        Op.MSTORE(64, 0, new_memory_size=96, old_memory_size=0)
        + FRESH_SET(SLOT_X, 1)
        + FRESH_SET(SLOT_Y, 1)
        + Op.MSTORE(0, Op.GAS)
        + call
        + Op.MSTORE(32, Op.GAS)
        + probe
        + Op.MSTORE(64, Op.GAS)
        + FRESH_SET(SLOT_RESULT, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
        + FRESH_SET(SLOT_PROBE_RESULT, Op.SUB(Op.MLOAD(32), Op.MLOAD(64)))
    )
    contract = pre.deploy_contract(code=code)

    # A window runs from one GAS read to the next: the store of the
    # first read, the window's code and the second read.
    stamp_cost = Op.MSTORE(0, Op.GAS).gas_cost(fork)
    call_cost = (
        stamp_cost
        + call.execution_cost(fork)
        + child_code.execution_cost(fork)
    )
    probe_cost = stamp_cost + probe.execution_cost(fork)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=(
            reservoir_slots * Op.SSTORE(new_value=1).state_cost(fork)
        ),
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(
            storage={
                SLOT_X: 0,
                SLOT_Y: 0,
                SLOT_PROBE: 1,
                SLOT_RESULT: call_cost,
                SLOT_PROBE_RESULT: probe_cost,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_call_opcodes(
    # A static child cannot write, so it can never refund.
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_parks_in_reservoir_at_a_call(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Opcode,
) -> None:
    """
    Test a call merging a refund parks it in the reservoir.

    A holder contract owns the cleared slot, so every dispatch reaches
    it the same way. The clearing window and the no-op window cost the
    same: the refund stays in the reservoir across the merge.
    """
    holder = deploy_slot_holder(pre)
    set_slot = Op.POP(Op.CALL(address=holder, args_size=1))
    clearer = pre.deploy_contract(code=Op.CALL(address=holder))
    window = Op.POP(call_opcode(address=clearer))
    contract = pre.deploy_contract(
        code=clearing_probe_code(set_slot, [window] * 3)
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    # Under the merge-time repayment of ethereum/EIPs#12265 the
    # clearing window repays the spill and the excess wraps to minus
    # the slot's state cost.
    post = {
        holder: Account(storage={SLOT_X: 0}),
        contract: Account(
            storage={SLOT_MARKER: 1, SLOT_INCREASED: 0, SLOT_RESULT: 0}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_parks_in_reservoir_at_a_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Opcode,
) -> None:
    """
    Test a create merging a refund parks it in the reservoir.

    The initcode reaches a holder contract that clears its own slot.
    The refund stays in the reservoir across the merge, where the next
    window's account creation charge draws on it, so the clearing
    window costs one slot's state gas more than the no-op window.
    """
    holder = deploy_slot_holder(pre)
    set_slot = Op.POP(Op.CALL(address=holder, args_size=1))
    # Pushing the zero arguments with PUSH0 keeps the initcode inside a
    # single memory word.
    initcode = Op.CALL(
        Op.GAS, holder, Op.PUSH0, Op.PUSH0, Op.PUSH0, Op.PUSH0, Op.PUSH0
    )
    mstore_value, size = init_code_at_high_bytes(initcode)

    # The probe measures with memory below 96, so the initcode sits
    # above it.
    code_offset = 96

    def window(salt: int) -> Bytecode:
        # A repeated CREATE2 salt would collide with the account the
        # previous window created.
        if create_opcode == Op.CREATE2:
            return Op.POP(Op.CREATE2(0, code_offset, size, salt))
        return Op.POP(Op.CREATE(0, code_offset, size))

    contract = pre.deploy_contract(
        code=Op.MSTORE(code_offset, mstore_value)
        + clearing_probe_code(set_slot, [window(salt) for salt in range(3)])
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    cleared = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    # Under the merge-time repayment of ethereum/EIPs#12265 the refund
    # reaches `gas_left` instead, so the excess flips sign.
    post = {
        holder: Account(storage={SLOT_X: 0}),
        contract: Account(
            storage={
                SLOT_MARKER: 1,
                SLOT_INCREASED: 0,
                SLOT_RESULT: cleared.state_refund(fork),
            }
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
