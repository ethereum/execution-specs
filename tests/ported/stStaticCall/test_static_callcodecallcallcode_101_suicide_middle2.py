"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddle2Filler.json

callee code:
    push20 0xcc7b2c7c17e1dd7940b1aa2f4b3e55d7bd662608
    selfdestruct
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3
    push2 0xc350
    callcode
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_2 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x3a5852e2f86bae6627a307298c4bf906ada12419
    push3 0x0186a0
    staticcall
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    callvalue
    push20 0x620b381d01cbd812ffb798ab35a1a316bde90ce6
    push3 0x0249f0
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddle2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_suicide_middle2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xcc7b2c7c17e1dd7940b1aa2f4b3e55d7bd662608")
    callee = Address("0x3a5852e2f86bae6627a307298c4bf906ada12419")
    callee_1 = Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3")
    callee_2 = Address("0x620b381d01cbd812ffb798ab35a1a316bde90ce6")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH20[0xcc7b2c7c17e1dd7940b1aa2f4b3e55d7bd662608] + Op.SELFDESTRUCT
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3]
        + Op.PUSH2[0xc350] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3a5852e2f86bae6627a307298c4bf906ada12419] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.PUSH20[0x620b381d01cbd812ffb798ab35a1a316bde90ce6]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
