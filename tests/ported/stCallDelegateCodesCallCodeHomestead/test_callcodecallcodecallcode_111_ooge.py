"""
DELEGATE -> DELEGATE -> OOG DELEGATE -> CODE OOG

Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGEFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x69a0017a51ad556682f48b32235d0b61abdf4da4
    push3 0x0c3500
    delegatecall
    push1 0x00
    sstore
    stop

callee code:
    push1 0x01
    push1 0x03
    sstore
    push3 0x2fffff
    push1 0x00
    sha3
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x1dd747f92062bb53bb8e867ec2902792435f1748
    push3 0x061a80
    delegatecall
    push1 0x02
    sstore
    push1 0x01
    push1 0x0b
    sstore
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x3e423a7b1fba04d0c3f9423a3ae2a180d2878d5b
    push3 0x0927c0
    delegatecall
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
    ["tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecallcode_111_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """DELEGATE -> DELEGATE -> OOG DELEGATE -> CODE OOG."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x0e7163a4a90126c4a13e52f48e84c74600e844da")
    callee = Address("0x1dd747f92062bb53bb8e867ec2902792435f1748")
    callee_1 = Address("0x3e423a7b1fba04d0c3f9423a3ae2a180d2878d5b")
    callee_2 = Address("0x69a0017a51ad556682f48b32235d0b61abdf4da4")

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
        + Op.PUSH20[0x69a0017a51ad556682f48b32235d0b61abdf4da4] + Op.PUSH3[0xc3500]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH3[0x2fffff]
        + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1dd747f92062bb53bb8e867ec2902792435f1748] + Op.PUSH3[0x61a80]
        + Op.DELEGATECALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xb]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x3e423a7b1fba04d0c3f9423a3ae2a180d2878d5b] + Op.PUSH3[0x927c0]
        + Op.DELEGATECALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
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
