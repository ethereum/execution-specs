"""
Test_codecopy_dejavu2.

Ported from:
state_tests/stMemoryTest/codecopy_dejavu2Filler.json
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
    ["state_tests/stMemoryTest/codecopy_dejavu2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_codecopy_dejavu2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_codecopy_dejavu2."""
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

    # Source: yul
    # berlin { codecopy(0x1f, 0x010000000000000001, 0x0a) let mem := mload(0) if eq(mem, 0) {stop()} }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(
            dest_offset=0x1F, offset=0x10000000000000001, size=0xA
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc165257d26f9435cbd00d8e2825ff173393d3b31"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x271000000000)

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=100000,
        value=10,
        gas_price=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
