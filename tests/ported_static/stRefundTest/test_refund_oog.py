"""
Test a transaction one gas short of clearing a storage slot.

Ported from:
state_tests/stRefundTest/refund_OOGFiller.json

@manually-enhanced: Do not overwrite. The gas limit is one less than the
intrinsic cost of the value transfer plus the cold SSTORE clear, from the
fork's gas model. The fee recipient's priority fee is checked with `Tip`.
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
    ["state_tests/stRefundTest/refund_OOGFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Run out of gas on the slot clear: no refund and no value moves."""
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

    # One gas short of the clear (see test_refund_no_oog_1).
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=fork.transaction_intrinsic_cost_calculator()(
            sends_value=True
        )
        + code.gas_cost(fork)
        - 1,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    # The whole gas limit is consumed and nothing is refunded.
    post = {
        target: Account(storage={1: 1}, balance_change=0),
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
    }
    # Before the Merge the coinbase also receives the block reward.
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=tx.gas_limit) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
