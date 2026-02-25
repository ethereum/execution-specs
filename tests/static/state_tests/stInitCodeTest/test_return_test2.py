"""
Ported from:
tests/static/state_tests/stInitCodeTest/ReturnTest2Filler.json

contract code:
    push1 0x15
    push1 0x00
    mstore
    push1 0x20
    push1 0x20
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b
    push2 0x1b58
    call
    pop
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    ... (4 more instructions)

callee code:
    push1 0x00
    calldataload
    push1 0x03
    mul
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
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
    ["tests/static/state_tests/stInitCodeTest/ReturnTest2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_return_test2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x15] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.PUSH2[0x1b58]
        + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x989680, nonce=0)
    pre[callee] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x3] + Op.MUL + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=250000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
