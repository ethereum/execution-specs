"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    callvalue
    push20 0xb60789f240ac9f12fcde1e4bbd5042a7f30932d4
    push3 0x0249f0
    callcode
    push1 0x00
    sstore
    gas
    push1 0x01
    sstore
    stop

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216
    push2 0xc350
    staticcall
    pop
    push20 0x44d09ddf088dd88c0e91fa7ef74973ff94ad7414
    selfdestruct
    stop

callee_1 code:
    push1 0x01
    push1 0x02
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
    ["tests/static/state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json"],
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
def test_static_callcodecall_10_suicide_end2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x44d09ddf088dd88c0e91fa7ef74973ff94ad7414")
    callee = Address("0xb60789f240ac9f12fcde1e4bbd5042a7f30932d4")
    callee_1 = Address("0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216")

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
        + Op.CALLVALUE + Op.PUSH20[0xb60789f240ac9f12fcde1e4bbd5042a7f30932d4]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.POP
        + Op.PUSH20[0x44d09ddf088dd88c0e91fa7ef74973ff94ad7414] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE + Op.STOP,
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
