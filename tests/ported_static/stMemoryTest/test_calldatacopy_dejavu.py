"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryTest/calldatacopy_dejavuFiller.json
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
    sender = EOA(
        key=0x7DD1D0EC78FE936B0E88F8C21226F51F048579915C7BAFF1C5D7FD84B2139BF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=52949672960,
    )

    pre[sender] = Account(balance=0x271000000000)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0xFF]
            + Op.CALLDATACOPY(
                dest_offset=0xFFFFFFF, offset=0xFFFFFFF, size=0xFF
            )
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xcb76ef53a4eb6ccf604daed675e91df8a0b544f8"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=10,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
