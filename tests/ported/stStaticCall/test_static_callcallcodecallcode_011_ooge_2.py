"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json

callee code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    callcode
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    stop

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x11a4a9dad43e6ed44e108eaf7fb160f9835068f4
    push3 0x0249f0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_2 code:
    push1 0x0b
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push2 0x4e34
    callcode
    pop
    push1 0x01
    push1 0x0d
    mstore
    stop

callee_3 code:
    push1 0x0b
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push2 0x4e34
    callcode
    pop
    push1 0x01
    push1 0x0d
    mstore
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000bb2e6e56806816e94a356b0f0c8e53f98e44d6ad",
        "000000000000000000000000f43b4e8b779078758104039080947f8f74e663d3",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x6e143211e9d36eaeebe65f6ed69d6c28500040d6")
    callee = Address("0x11a4a9dad43e6ed44e108eaf7fb160f9835068f4")
    callee_1 = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_2 = Address("0xbb2e6e56806816e94a356b0f0c8e53f98e44d6ad")
    callee_3 = Address("0xf43b4e8b779078758104039080947f8f74e663d3")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x11a4a9dad43e6ed44e108eaf7fb160f9835068f4] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xb] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH2[0x4e34]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0xd] + Op.MSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xb] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH2[0x4e34]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0xd] + Op.MSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=172000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
