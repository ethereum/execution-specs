"""
test_extcodecopy_dejavu

Ported from:
state_tests/stMemoryTest/extcodecopy_dejavuFiller.json
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
    ["state_tests/stMemoryTest/extcodecopy_dejavuFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodecopy_dejavu(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_extcodecopy_dejavu"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x7dd1d0ec78fe936b0e88f8c21226f51f048579915c7baff1c5d7fd84b2139bf1
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
    # 0x60FF60FF630FFFFFFF630FFFFFFF3C
    target = pre.deploy_contract(
        code=Op.EXTCODECOPY(address=0xfffffff, dest_offset=0xfffffff, offset=0xff, size=0xff),
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xe15245403ddc4d3674436cf955358a73d67e226a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x271000000000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
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
