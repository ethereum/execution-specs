"""
CALL -> (DELEGATE -> DELEGATE -> CODE) OOG

Ported from:
tests/static/state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMAfterFiller.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xda11fdf0ce02240c6b4711f56afcd9763b44d3dc
    push3 0x0927c0
    delegatecall
    push1 0x01
    sstore
    push3 0x2fffff
    push1 0x00
    sha3
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    sstore
    stop

callee_2 code:
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

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x1adae71ad3aeec97978e38be04da2a1773dfc506
    push3 0x0c3500
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x0b
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
    ["tests/static/state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMAfterFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecallcode_011_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL -> (DELEGATE -> DELEGATE -> CODE) OOG."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xe54ccfa5e33a84943997885f0ab9c19c587d8c4f")
    callee = Address("0x1adae71ad3aeec97978e38be04da2a1773dfc506")
    callee_1 = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")
    callee_2 = Address("0xda11fdf0ce02240c6b4711f56afcd9763b44d3dc")

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
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xda11fdf0ce02240c6b4711f56afcd9763b44d3dc] + Op.PUSH3[0x927c0]
        + Op.DELEGATECALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH3[0x2fffff]
        + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb126c622075b1189fb6c45e851641cfaddf65b36] + Op.PUSH3[0x61a80]
        + Op.DELEGATECALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x1adae71ad3aeec97978e38be04da2a1773dfc506]
        + Op.PUSH3[0xc3500] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0xb] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

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
