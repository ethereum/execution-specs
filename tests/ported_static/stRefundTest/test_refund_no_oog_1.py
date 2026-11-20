"""
Test a transaction with exactly enough gas to clear a storage slot.

Ported from:
state_tests/stRefundTest/refund_NoOOG_1Filler.json

@manually-enhanced: Do not overwrite. The gas limit is the intrinsic
cost plus the cold SSTORE clear, and the gas used subtracts the refund
capped at `max_refund_quotient`, all from the fork's gas model. The fee
recipient's priority fee is checked with `Tip`.
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
    ["state_tests/stRefundTest/refund_NoOOG_1Filler.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_no_oog_1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Clear a cold slot with no gas to spare; the refund still applies."""
    sender = pre.fund_eoa()

    code = (
        Op.SSTORE(
            key=0x1,
            value=0x0,
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=0,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(code=code, storage={1: 1})

    # The gas limit covers the clear exactly; one gas less runs out of
    # gas (see test_refund_oog).
    gas_before_refund = fork.transaction_intrinsic_cost_calculator()() + (
        code.gas_cost(fork)
    )
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_before_refund,
        protected=fork.supports_protected_txs(),
    )

    refund = min(
        code.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {
        target: Account(storage={}),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }
    # Before the Merge the coinbase also receives the block reward.
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
