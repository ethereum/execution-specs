"""
Apparently this test was testing theoretical issue occur when tr gas > block gas limit overflow. no longer the case

Ported from:
tests/static/state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_overflow_gas_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Apparently this test was testing theoretical issue occur when tr gas > block gas limit overflow. no longer the case."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xde1dfd9a06b67489748eeab5f2ae651c85bc1654")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x4fec000000000139c, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4c30106c229cd77a61e9eab5fcee11cc912bf94f785ee56f406817744bb6a074"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=501,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
