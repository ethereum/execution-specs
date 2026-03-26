"""
test_high_gas_price_paris

Ported from:
state_tests/stTransactionTest/HighGasPriceParisFiller.yml
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
    ["state_tests/stTransactionTest/HighGasPriceParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_high_gas_price_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_high_gas_price_paris"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0 = Address("0x76fae819612a29489a1a43208613d8f8557b8898")  # noqa: E501
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3b9aca00)
    pre[addr_0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0] = Account(balance=10)


    tx = Transaction(
        sender=sender,
        to=addr_0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0,
        data=b'',
        gas_limit=21000,
        value=1,
        nonce=0,
        gas_price=5513909011300771210646237381366090850155713555506693525688456381329244268,
        error=[TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW],
    )

    post = {
        coinbase: Account.NONEXISTENT,
        addr_0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0: Account(balance=10),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
