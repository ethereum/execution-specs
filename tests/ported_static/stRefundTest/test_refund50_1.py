"""
Test that the refund for clearing five storage slots is capped.

Ported from:
state_tests/stRefundTest/refund50_1Filler.json

@manually-enhanced: Do not overwrite. The expected gas used is computed from
the fork's gas model: intrinsic cost plus the five cold SSTORE clears, minus
their refund capped at `max_refund_quotient`. The fee recipient's priority fee
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


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund50_1Filler.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund50_1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Clear five cold storage slots; the refund exceeds the cap."""
    sender = pre.fund_eoa()

    # Each SSTORE clears a cold slot that was set in the pre-state.
    cold_clear = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=0
    )
    code = (
        cold_clear(key=0x1, value=0x0)
        + cold_clear(key=0x2, value=0x0)
        + cold_clear(key=0x3, value=0x0)
        + cold_clear(key=0x4, value=0x0)
        + cold_clear(key=0x5, value=0x0)
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=code,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=100000,
        protected=fork.supports_protected_txs(),
    )

    gas_before_refund = (
        fork.transaction_intrinsic_cost_calculator()() + code.gas_cost(fork)
    )
    refund = min(
        code.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {
        target: Account(storage={}),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
