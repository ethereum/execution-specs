"""
Test_transaction_data_costs652.

Ported from:
state_tests/stTransactionTest/TransactionDataCosts652Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork, Prague

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/TransactionDataCosts652Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_transaction_data_costs652(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_transaction_data_costs652."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x989680)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    tx_data = [
        Bytes("00000000000000000000112233445566778f32"),
    ]
    # EIP-7976 (enabled with EIP-8037 on Amsterdam) increases the
    # calldata floor cost per byte, pushing the g0 budget below the
    # new intrinsic. Shift gas_limits by the intrinsic delta versus
    # the pre-7976 baseline so the tight / loose budgets still hold.
    current_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data[d]
    )
    baseline_intrinsic = Prague.transaction_intrinsic_cost_calculator()(
        calldata=tx_data[d]
    )
    intrinsic_delta = current_intrinsic - baseline_intrinsic
    tx_gas = [22000 + intrinsic_delta, 72000 + intrinsic_delta]

    floor_cost = fork.transaction_data_floor_cost_calculator()(data=tx_data[d])
    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=tx_data[d],
        gas_limit=max(tx_gas[g], floor_cost),
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
