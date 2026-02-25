"""
callcode with high value fails

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callcodeWithHighValueFiller.json

callee code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x37
    push1 0x00
    mstore8
    push1 0x02
    push1 0x00
    return

contract code:
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push8 0x0de0b6b3a7640001
    push20 0x0896f13e800125c0ccec44f3c434335f0a97bc1b
    push2 0xc350
    callcode
    push1 0x00
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/callcodeWithHighValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_with_high_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """callcode with high value fails."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x177bd06bad8f3fe1b5d335d0aba2f2a6b18b2fc6")
    callee = Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x37] + Op.PUSH1[0x0]
        + Op.MSTORE8 + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH8[0xde0b6b3a7640001]
        + Op.PUSH20[0x896f13e800125c0ccec44f3c434335f0a97bc1b] + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
