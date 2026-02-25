"""
CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE

Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xb5104f0f7758ce0caac73f593c6d63eb9a5ef905
    push3 0x0249f0
    callcode
    push1 0x00
    sstore
    stop

callee code:
    push1 0x01
    push1 0x03
    sstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xc176d297ff74c0f684b73d6cc8617e7f5ffe34fe
    push2 0x9c90
    delegatecall
    push1 0x01
    sstore
    push1 0x01
    push1 0x0b
    sstore
    stop

callee_2 code:
    push3 0x2fffff
    push1 0x00
    sha3
    pop
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xb126c622075b1189fb6c45e851641cfaddf65b36
    push2 0x4e34
    delegatecall
    push1 0x02
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
    ["tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecallcode_011_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xa74ca10b765dcda3b60687f73f2881e2a56eda64")
    callee = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")
    callee_1 = Address("0xb5104f0f7758ce0caac73f593c6d63eb9a5ef905")
    callee_2 = Address("0xc176d297ff74c0f684b73d6cc8617e7f5ffe34fe")

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
        + Op.PUSH1[0x0] + Op.PUSH20[0xb5104f0f7758ce0caac73f593c6d63eb9a5ef905]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc176d297ff74c0f684b73d6cc8617e7f5ffe34fe] + Op.PUSH2[0x9c90]
        + Op.DELEGATECALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xb]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.POP + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb126c622075b1189fb6c45e851641cfaddf65b36] + Op.PUSH2[0x4e34]
        + Op.DELEGATECALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=172000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
