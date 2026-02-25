"""
Ported from:
tests/static/state_tests/stMemoryTest/stackLimitPush31_1023Filler.json

contract code:
    push2 0x03fd
    push1 0x00
    mstore
    jumpdest
    push31 0x0102030405060708090a0102030405060708090a0102030405060708090a01
    push1 0x01
    push1 0x00
    mload
    sub
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x06
    jumpi
    stop
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
    ["tests/static/state_tests/stMemoryTest/stackLimitPush31_1023Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_stack_limit_push31_1023(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc102734f6a1e4747310179c0a0fc16e674aa901d")
    contract = Address("0x887fe5a55a7be422caf5816b6721c8bb9f8abbcb")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0x3fd] + Op.PUSH1[0x0] + Op.MSTORE + Op.JUMPDEST
        + Op.PUSH31[0x102030405060708090a0102030405060708090a0102030405060708090a01]
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x6] + Op.JUMPI + Op.STOP
        + Op.STOP
    ),
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
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
