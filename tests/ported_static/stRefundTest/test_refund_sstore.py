"""
Test the refund from clearing a single storage slot.

Ported from:
state_tests/stRefundTest/refundSSTOREFiller.yml

@manually-enhanced: Do not overwrite. The expected gas used is computed
from the fork's gas model: intrinsic cost plus the cold SSTORE clear,
minus its refund capped at `max_refund_quotient`.
The filler's calldata, access list, gas price and gas limit are dropped.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

STORED_VALUE = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundSSTOREFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
def test_refund_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Clear one cold storage slot and get the fork's refund for it."""
    sender = pre.fund_eoa()

    # The zero pushed as the value is reused as the key.
    code = (
        Op.SSTORE(
            key=Op.DUP1,
            value=0x0,
            key_warm=False,
            original_value=STORED_VALUE,
            current_value=STORED_VALUE,
            new_value=0,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(code=code, storage={0: STORED_VALUE})

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    gas_before_refund = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    ) + code.gas_cost(fork)
    refund = min(
        code.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {
        target: Account(storage={}),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }

    state_test(pre=pre, post=post, tx=tx)
