"""
CALL -> CALL -> OOG DELEGATE -> CODE 

Ported from:
tests/static/state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMBeforeFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x471072d55a5a95044c2326f0e94a6d8df5b8089e
    push3 0x0c3500
    call
    push1 0x00
    sstore
    stop

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xefe4727369c5f495aebf4ea778cc48d1155bf978
    push3 0x0927c0
    call
    push1 0x01
    sstore
    push1 0x01
    push1 0x0b
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
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
    push3 0x061a80
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
    ["tests/static/state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcallcode_001_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL -> CALL -> OOG DELEGATE -> CODE ."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x335b558774699d81f685543cfbcde5c4e5407686")
    callee = Address("0x471072d55a5a95044c2326f0e94a6d8df5b8089e")
    callee_1 = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")
    callee_2 = Address("0xefe4727369c5f495aebf4ea778cc48d1155bf978")

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
        + Op.PUSH1[0x0] + Op.PUSH20[0x471072d55a5a95044c2326f0e94a6d8df5b8089e]
        + Op.PUSH3[0xc3500] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xefe4727369c5f495aebf4ea778cc48d1155bf978]
        + Op.PUSH3[0x927c0] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0xb] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.POP + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb126c622075b1189fb6c45e851641cfaddf65b36] + Op.PUSH3[0x61a80]
        + Op.DELEGATECALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
