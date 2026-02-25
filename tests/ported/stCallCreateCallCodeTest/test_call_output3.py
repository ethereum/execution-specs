"""
check the output memory after call

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callOutput3Filler.json

callee code:
    push1 0x01
    push1 0x01
    add
    push1 0x00
    sstore

contract code:
    push32 0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xbcc1197ccd23a97607f2f96d031f3432e0d16a02
    push3 0x0249f0
    call
    pop
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/callOutput3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_output3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """check the output memory after call."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd4e4bfa87dc8f20706bf63f45861945315be24f0")
    callee = Address("0xbcc1197ccd23a97607f2f96d031f3432e0d16a02")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.SSTORE,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbcc1197ccd23a97607f2f96d031f3432e0d16a02] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=b"",
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
