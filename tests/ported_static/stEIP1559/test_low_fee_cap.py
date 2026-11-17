"""
Reject a transaction whose fee cap is below the base fee.

Ported from:
state_tests/stEIP1559/lowFeeCapFiller.yml
state_tests/stEIP1559/lowGasPriceOldTypesFiller.yml

@manually-enhanced: Do not overwrite. Merged over the transaction type.
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP1559/lowFeeCapFiller.yml",
        "state_tests/stEIP1559/lowGasPriceOldTypesFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(reason="Expects the base fee of the test env")
)
@pytest.mark.exception_test
@pytest.mark.parametrize("tx_type", [0, 1, 2])
def test_low_fee_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
) -> None:
    """Send a transaction whose gas price or fee cap is one below the fee."""
    base_fee = Environment().set_fork_requirements(fork).base_fee_per_gas
    assert base_fee is not None
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(0, 2) + Op.STOP)

    fee = int(base_fee) - 1
    fees = (
        {"max_fee_per_gas": fee, "max_priority_fee_per_gas": 0}
        if tx_type == 2
        else {"gas_price": fee}
    )
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=target,
        value=100_000,
        error=TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
        **fees,
    )

    state_test(pre=pre, post={}, tx=tx)
