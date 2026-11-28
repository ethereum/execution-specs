"""
Verify that a storage-clear refund is lost when the sub-call making it
runs out of gas.

Ported from:
state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json

@manually-enhanced: Do not overwrite. The gas used is derived from the fork:
intrinsic cost plus the caller's code plus the whole sub-call grant, which the
starved callee consumes; no refund survives. The fee recipient's priority fee
and block reward are checked with `Tip` and `BlockReward`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BlockReward,
    Environment,
    Fork,
    GasFee,
    StateTestFiller,
    Tip,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# One gas short of the callee's cold storage clear on Cancun.
CALL_GAS = 5005


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallA_notEnoughGasInCallFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_call_a_not_enough_gas_in_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Starve a sub-call clearing a storage slot so its refund is lost."""
    sender = pre.fund_eoa()

    callee_code = Op.SSTORE(
        key=0x1, value=0x0, key_warm=False, original_value=1, new_value=0
    )
    callee = pre.deploy_contract(
        code=callee_code + Op.STOP,
        storage={1: 1},
    )
    assert callee_code.gas_cost(fork) > CALL_GAS, "callee must run out of gas"

    # The failed call leaves slot 0 unchanged at zero.
    caller_code = Op.SSTORE(
        key=0x0,
        value=Op.CALL(gas=CALL_GAS, address=callee, address_warm=False),
        key_warm=False,
        original_value=0,
        new_value=0,
    )
    caller = pre.deploy_contract(
        code=caller_code + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=85000,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    # The callee runs out of gas, consuming the whole grant, and its
    # reverted clear earns no refund.
    gas_used = (
        fork.transaction_intrinsic_cost_calculator()(sends_value=True)
        + caller_code.gas_cost(fork)
        + CALL_GAS
    )

    post = {
        caller: Account(storage={1: 1}, balance_change=tx.value),
        callee: Account(storage={1: 1}),
        sender: Account(balance_change=-tx.value - GasFee(tx, gas=gas_used)),
    }
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
