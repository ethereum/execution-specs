"""
Test a value transfer into a self-destructing contract that runs out of gas.

Ported from:
state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json

@manually-enhanced: Do not overwrite. The gas limit leaves the frame one
gas short of its first opcode, derived from the fork's intrinsic cost and
the push's `gas_cost`. The fee recipient's priority fee is checked with
`Tip`.
"""

import pytest
from execution_testing import (
    Account,
    Address,
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

CONTRACT_BALANCE = 0xDE0B6B3A7640000
BENEFICIARY = Address(0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_tx_to_suicide_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Run out of gas before the self-destruct: nothing moves or refunds."""
    sender = pre.fund_eoa()

    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=BENEFICIARY) + Op.STOP,
        storage={1: 1},
        balance=CONTRACT_BALANCE,
    )

    # The frame cannot pay for the push of the beneficiary address.
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=fork.transaction_intrinsic_cost_calculator()(
            sends_value=True
        )
        + Op.PUSH20.gas_cost(fork)
        - 1,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    # The whole gas limit is consumed and nothing is refunded.
    post = {
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
        target: Account(storage={1: 1}, balance=CONTRACT_BALANCE),
        BENEFICIARY: Account.NONEXISTENT,
    }
    # Before the Merge the coinbase also receives the block reward.
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=tx.gas_limit) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
