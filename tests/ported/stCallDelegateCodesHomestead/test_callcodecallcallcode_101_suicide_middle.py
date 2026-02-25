"""
Ported from:
tests/static/state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1000000000000000000000000000000000000001
    push3 0x0249f0
    delegatecall
    push1 0x00
    sstore
    stop

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x1000000000000000000000000000000000000002
    push3 0x0186a0
    call
    push1 0x01
    sstore
    stop

callee_1 code:
    push20 0x1000000000000000000000000000000000000000
    selfdestruct
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1000000000000000000000000000000000000003
    push2 0xc350
    delegatecall
    push1 0x02
    sstore
    stop

callee_2 code:
    push1 0x01
    push1 0x03
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
    ["tests/static/state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000000")
    callee = Address("0x1000000000000000000000000000000000000001")
    callee_1 = Address("0x1000000000000000000000000000000000000002")
    callee_2 = Address("0x1000000000000000000000000000000000000003")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1000000000000000000000000000000000000001] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x1000000000000000000000000000000000000002]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH20[0x1000000000000000000000000000000000000000] + Op.SELFDESTRUCT
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1000000000000000000000000000000000000003] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
