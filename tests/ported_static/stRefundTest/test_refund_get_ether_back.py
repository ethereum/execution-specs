"""
Test a value transfer into a contract that clears a storage slot.

Ported from:
state_tests/stRefundTest/refund_getEtherBackFiller.json

@manually-enhanced: Do not overwrite. The expected gas used is computed
from the fork's gas model: intrinsic cost of the value transfer plus the
cold SSTORE clear, minus its refund capped at `max_refund_quotient`. The
fee recipient's priority fee is checked with `Tip`.
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
    ["state_tests/stRefundTest/refund_getEtherBackFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_get_ether_back(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Send value to a contract that clears a cold slot and get a refund."""
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

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=228500,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    gas_before_refund = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True
    ) + code.gas_cost(fork)
    refund = min(
        code.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {
        target: Account(storage={}, balance_change=tx.value),
        sender: Account(balance_change=-tx.value - GasFee(tx, gas=gas_used)),
    }
    # Before the Merge the coinbase also receives the block reward.
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
