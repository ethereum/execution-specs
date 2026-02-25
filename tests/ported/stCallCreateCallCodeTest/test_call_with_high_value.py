"""
call with value and not enough value to send

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json

callee code:
    push1 0x01
    push1 0x02
    sstore
    stop

contract code:
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push8 0x0de0b6b3a7640001
    push20 0x9d8c3fed067968360493f6deb5b169a720dac8a2
    push3 0x0249f0
    call
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call with value and not enough value to send."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xccc6849cd07c3e5b61ab6d7e798d3c4007615284")
    callee = Address("0x9d8c3fed067968360493f6deb5b169a720dac8a2")

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
        code=Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH8[0xde0b6b3a7640001]
        + Op.PUSH20[0x9d8c3fed067968360493f6deb5b169a720dac8a2] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
