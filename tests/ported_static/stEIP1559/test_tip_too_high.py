"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP1559/tipTooHighFiller.yml
"""

import pytest
from execution_testing import (
    Address,
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
@pytest.mark.pre_alloc_mutable
def test_tip_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # london
    # {
    #     sstore(0, add(1,1))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=400000,
        value=0x186A0,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=1001,
        nonce=1,
        access_list=[],
        error=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
