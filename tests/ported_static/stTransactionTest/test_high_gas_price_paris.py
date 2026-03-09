"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/HighGasPriceParisFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stTransactionTest/HighGasPriceParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_high_gas_price_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )
    contract = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[contract] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_price=5513909011300771210646237381366090850155713555506693525688456381329244268,  # noqa: E501
        value=1,
        error=[
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW,
        ],
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
