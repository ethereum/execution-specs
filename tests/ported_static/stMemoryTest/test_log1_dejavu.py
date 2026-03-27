"""
Test_log1_dejavu.

Ported from:
state_tests/stMemoryTest/log1_dejavuFiller.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/log1_dejavuFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log1_dejavu(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_log1_dejavu."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x7DD1D0EC78FE936B0E88F8C21226F51F048579915C7BAFF1C5D7FD84B2139BF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=52949672960,
    )

    # Source: raw
    # 0x60FF60FF630FFFFFFFA1
    target = pre.deploy_contract(  # noqa: F841
        code=Op.LOG1(offset=0xFFFFFFF, size=0xFF, topic_1=0xFF),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x2e5dd28ace62cb4fc05fc800ded494a6275107ac"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x271000000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=b"",
        gas_limit=100000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
