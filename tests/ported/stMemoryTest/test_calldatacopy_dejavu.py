"""
Ported from:
tests/static/state_tests/stMemoryTest/calldatacopy_dejavuFiller.json

contract code:
    push1 0xff
    push1 0xff
    push4 0x0fffffff
    push4 0x0fffffff
    calldatacopy
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stMemoryTest/calldatacopy_dejavuFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_calldatacopy_dejavu(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x894d19064bdc4e212b2e634e18a2b765d52e9b54")
    contract = Address("0xcb76ef53a4eb6ccf604daed675e91df8a0b544f8")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=52949672960,
    )

    pre[sender] = Account(balance=0x271000000000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH4[0xfffffff] + Op.PUSH4[0xfffffff]
        + Op.CALLDATACOPY
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x7dd1d0ec78fe936b0e88f8c21226f51f048579915c7baff1c5d7fd84b2139bf1"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
