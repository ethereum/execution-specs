"""
Test_high_gas_price_paris.

Ported from:
state_tests/stTransactionTest/HighGasPriceParisFiller.yml
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
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/HighGasPriceParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
def test_high_gas_price_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_high_gas_price_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Bytes(""),
        value=1,
        gas_price=5513909011300771210646237381366090850155713555506693525688456381329244268,  # noqa: E501
        error=[
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW,
        ],
    )

    post = {
        coinbase: Account.NONEXISTENT,
        addr: Account(balance=10),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
