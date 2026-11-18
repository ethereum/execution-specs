"""
Verify that a storage-clear refund earned in a sub-call is lost when the
calling frame then runs out of gas.

Ported from:
state_tests/stRefundTest/refund_CallA_OOGFiller.json

@manually-enhanced: Do not overwrite. The sub-call grant is the callee's fork-
derived cost, so it succeeds and earns its refund on every fork, and the
transaction gas limit is one gas short of finishing, so the caller's final
SSTORE runs out of gas. The fee recipient's priority fee and block reward are
checked with `Tip` and `BlockReward`.
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


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallA_OOGFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_call_a_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Run out of gas after a sub-call clears a storage slot."""
    sender = pre.fund_eoa()

    callee_code = Op.SSTORE(
        key=0x1, value=0x0, key_warm=False, original_value=1, new_value=0
    )
    callee = pre.deploy_contract(
        code=callee_code + Op.STOP,
        storage={1: 1},
    )
    # Grant the callee exactly what it needs to clear its slot.
    call_gas = callee_code.gas_cost(fork)
    assert callee_code.refund(fork) > 0, "the callee must earn a refund"

    # Storing the call's result in a fresh slot is what runs out of gas.
    caller_code = Op.SSTORE(
        key=0x0,
        value=Op.CALL(
            gas=call_gas,
            address=callee,
            address_warm=False,
            inner_call_cost=call_gas,
        ),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    caller = pre.deploy_contract(
        code=caller_code + Op.STOP,
        storage={1: 1},
    )

    # One gas short of completing the transaction: everything but the
    # last gas of the caller's final SSTORE is paid for.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(sends_value=True)
    tx_gas_limit = intrinsic + caller_code.gas_cost(fork) - 1

    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=tx_gas_limit,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    # The whole transaction reverts and consumes its entire gas limit, so
    # neither the value transfer nor the callee's clear (and refund) stay.
    post = {
        caller: Account(storage={1: 1}, balance_change=0),
        callee: Account(storage={1: 1}),
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
    }
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=tx.gas_limit) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
