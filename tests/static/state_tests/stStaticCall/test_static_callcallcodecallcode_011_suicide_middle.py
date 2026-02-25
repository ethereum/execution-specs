"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json

callee code:
    push1 0x01
    push1 0x03
    mstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x92d7028788caa240253b7b2a92386464690cdc72
    push3 0x0249f0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xeca01d36dbe4f4ab283a49016efa370bac7e7346
    push3 0x0186a0
    delegatecall
    stop

callee_2 code:
    push20 0x569cdc3b32cc3f9747bbde39fd70fead591d2f0d
    selfdestruct
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3
    push2 0xc350
    delegatecall
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x569cdc3b32cc3f9747bbde39fd70fead591d2f0d")
    callee = Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3")
    callee_1 = Address("0x92d7028788caa240253b7b2a92386464690cdc72")
    callee_2 = Address("0xeca01d36dbe4f4ab283a49016efa370bac7e7346")

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
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x92d7028788caa240253b7b2a92386464690cdc72] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xeca01d36dbe4f4ab283a49016efa370bac7e7346] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH20[0x569cdc3b32cc3f9747bbde39fd70fead591d2f0d] + Op.SELFDESTRUCT
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
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
