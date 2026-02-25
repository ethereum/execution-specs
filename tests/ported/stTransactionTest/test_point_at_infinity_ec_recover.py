"""
Ported from:
tests/static/state_tests/stTransactionTest/PointAtInfinityECRecoverFiller.yml
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
    ["tests/static/state_tests/stTransactionTest/PointAtInfinityECRecoverFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_point_at_infinity_ec_recover(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xb9f36f1cb467544974bb7e0f5e1f0a499d4e6d7d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[contract] = Account(
        balance=0xffffffff,
        nonce=0,
        code=bytes.fromhex(
        "6000805160206065833981519152600052601b6020527f79be667ef9dcbbac55a06295ce"
        "870b07029bfcdb2dce28d959f2815b16f817986040526000805160206065833981519152"
        "60605260206000608081806001620f4240f160005560005160015500fe6b8d2c81b11b2d"
        "699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9"
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
