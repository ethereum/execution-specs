"""
Ported from:
tests/static/state_tests/stReturnDataTest/returndatacopy_initial_big_sumFiller.json

contract code:
    push15 0x112233445566778899aabbccddeeff
    push1 0x00
    mstore
    push1 0x3f
    push1 0x02
    exp
    push1 0x3f
    push1 0x02
    exp
    push1 0x00
    returndatacopy
    push1 0x00
    mload
    push1 0x00
    sstore
    stop
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
    ["tests/static/state_tests/stReturnDataTest/returndatacopy_initial_big_sumFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_initial_big_sum(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc102734f6a1e4747310179c0a0fc16e674aa901d")
    contract = Address("0x3c975790c6cbb489ae5eaf7af45202f98dffccdf")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH15[0x112233445566778899aabbccddeeff] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x3f] + Op.PUSH1[0x2] + Op.EXP + Op.PUSH1[0x3f] + Op.PUSH1[0x2]
        + Op.EXP + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
