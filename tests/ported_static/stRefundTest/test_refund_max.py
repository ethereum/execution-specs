"""
Test the maximum refund from clearing eight storage slots.

Ported from:
state_tests/stRefundTest/refundMaxFiller.yml

@manually-enhanced: Do not overwrite. The expected gas used is computed
from the fork's gas model: intrinsic cost plus the eight cold SSTORE
clears, minus their refund capped at `max_refund_quotient`.
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
    ["state_tests/stRefundTest/refundMaxFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
def test_refund_max(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Clear eight cold storage slots; the refund is capped."""
    sender = pre.fund_eoa()

    # Each SSTORE clears a cold slot that was set in the pre-state. The
    # zero pushed first is reused as the value of every clear.
    cold_clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=STORED_VALUE,
        current_value=STORED_VALUE,
        new_value=0,
    )
    code = (
        cold_clear(key=0x0, value=0x0)
        + cold_clear(key=0x1, value=0x0)
        + cold_clear(key=0x2, value=0x0)
        + cold_clear(key=0x3, value=0x0)
        + cold_clear(key=0x4, value=0x0)
        + cold_clear(key=0x5, value=0x0)
        + cold_clear(key=0x6, value=0x0)
        + cold_clear(key=0x7, value=0x0)
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(range(8), STORED_VALUE),
    )

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
