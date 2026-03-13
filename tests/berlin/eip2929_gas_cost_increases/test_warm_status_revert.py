"""
Tests that warm/cold access status is reverted when a sub-call reverts.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Conditional,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2929.md"
REFERENCE_SPEC_VERSION = "0e11417265a623adb680c527b15d0cb6701b870b"


@pytest.mark.valid_from("Berlin")
def test_storage_warm_status_reverted_by_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that storage slot warm status is reverted when a sub-call reverts.

    Inner self-call does SLOAD(0) and SSTORE(0, 2) then REVERTs. After
    revert, SLOAD(0) must be a cold access and storage[0] must still
    hold its original value.
    """
    env = Environment()

    # Inner behavior (no calldata): warm slot 0 via SLOAD+SSTORE, revert.
    inner_code = (
        Op.POP(Op.SLOAD(0)) + Op.SSTORE(0, 2) + Op.REVERT(offset=0, size=0)
    )

    # Overhead: PUSH instructions for the SLOAD key argument.
    sload_push_cost = (Op.PUSH1(0) * len(Op.SLOAD.kwargs)).gas_cost(fork)
    cold_sload_cost = Op.SLOAD(key_warm=False).gas_cost(fork)

    # After revert, measure gas of SLOAD(0) — should be cold.
    sload_measure = CodeGasMeasure(
        code=Op.SLOAD(0),
        overhead_cost=sload_push_cost,
        extra_stack_items=1,
        sstore_key=1,
        stop=False,
    )

    # Also verify storage[0] value (should still be 1).
    verify_value = Op.SSTORE(2, Op.SLOAD(0))

    # Outer behavior (has calldata): call self (inner), measure, verify.
    outer_code = (
        Op.POP(Op.CALL(gas=100_000, address=Op.ADDRESS))
        + sload_measure
        + verify_value
        + Op.STOP
    )

    code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=outer_code,
        if_false=inner_code,
    )

    contract = pre.deploy_contract(code, storage={0: 1})
    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            contract: Account(
                storage={0: 1, 1: cold_sload_cost, 2: 1},
            ),
        },
        tx=Transaction(
            sender=sender,
            to=contract,
            gas_limit=1_000_000,
            data=b"\x01",
        ),
    )


@pytest.mark.valid_from("Berlin")
def test_account_warm_status_reverted_by_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that account warm status is reverted when a sub-call reverts.

    Inner call does BALANCE(target) then REVERTs. After revert,
    BALANCE(target) in the outer call must be a cold access.
    """
    env = Environment()

    target = pre.fund_eoa(amount=1)

    # Inner: BALANCE(target) warms target, then reverts.
    inner = pre.deploy_contract(
        Op.POP(Op.BALANCE(target)) + Op.REVERT(offset=0, size=0)
    )

    # Overhead: PUSH for the BALANCE address argument.
    balance_push_cost = (Op.PUSH1(0) * len(Op.BALANCE.kwargs)).gas_cost(fork)
    cold_balance_cost = Op.BALANCE(address_warm=False).gas_cost(fork)

    # Outer: call inner (reverts), then measure BALANCE(target) gas.
    outer = pre.deploy_contract(
        Op.POP(Op.CALL(gas=100_000, address=inner))
        + CodeGasMeasure(
            code=Op.BALANCE(target),
            overhead_cost=balance_push_cost,
            extra_stack_items=1,
            sstore_key=0,
        )
    )

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={outer: Account(storage={0: cold_balance_cost})},
        tx=Transaction(
            sender=sender,
            to=outer,
            gas_limit=1_000_000,
        ),
    )
