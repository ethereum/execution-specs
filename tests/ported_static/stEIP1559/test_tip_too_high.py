"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP1559/tipTooHighFiller.yml
"""

import pytest
from execution_testing import (
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/tipTooHighFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
def test_tip_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa()

    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
    )

    env = Environment(base_fee_per_gas=1000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=400000,
        value=0x186A0,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=1001,
        access_list=[],
        error=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
