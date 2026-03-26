"""
test_calldatacopy_dejavu2

Ported from:
state_tests/stMemoryTest/calldatacopy_dejavu2Filler.json
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
    ["state_tests/stMemoryTest/calldatacopy_dejavu2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_calldatacopy_dejavu2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_calldatacopy_dejavu2"""
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

    # Source: yul
    # berlin { mstore8(0x1f, 0x42) calldatacopy(0x1f, 0, 0x0103) let mem := mload(0) if eq(mem,0x60) { stop() }  sstore(0xff, 0x0badc0ffee) }
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x1f, value=0x42)
        + Op.CALLDATACOPY(dest_offset=0x1f, offset=0x0, size=0x103)
        + Op.JUMPI(pc=0x20, condition=Op.EQ(Op.MLOAD(offset=0x0), 0x60))
        + Op.SSTORE(key=0xff, value=0xbadc0ffee) + Op.STOP + Op.JUMPDEST
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd6a7f80046f7576fa76ee5198426097f149e60ff"),  # noqa: E501
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
        target: Account(storage={255: 0xbadc0ffee}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
