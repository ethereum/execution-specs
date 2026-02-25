"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001_SuicideEnd2Filler.json

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
    push20 0xd7997c3f1aacabdc66b4da9461b9558b1787e01c
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
    push1 0x00
    push20 0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3
    push2 0xc350
    callcode
    pop
    push20 0xd7997c3f1aacabdc66b4da9461b9558b1787e01c
    selfdestruct
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x90e9b92c59a0e93d8ab0b7afbc945d6999a50a9b
    push3 0x0186a0
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001_SuicideEnd2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_suicide_end2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x569cdc3b32cc3f9747bbde39fd70fead591d2f0d")
    callee = Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3")
    callee_1 = Address("0x90e9b92c59a0e93d8ab0b7afbc945d6999a50a9b")
    callee_2 = Address("0xd7997c3f1aacabdc66b4da9461b9558b1787e01c")

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
        + Op.PUSH20[0xd7997c3f1aacabdc66b4da9461b9558b1787e01c] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3]
        + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH20[0xd7997c3f1aacabdc66b4da9461b9558b1787e01c] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x90e9b92c59a0e93d8ab0b7afbc945d6999a50a9b] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.STOP
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
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
