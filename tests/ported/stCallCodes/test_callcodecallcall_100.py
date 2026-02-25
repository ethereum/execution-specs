"""
CALLCODE -> CALL -> CALL-> code, params check

Ported from:
tests/static/state_tests/stCallCodes/callcodecallcall_100Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x03
    push20 0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c
    push3 0x03d090
    call
    push1 0x02
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    sstore
    caller
    push1 0x04
    sstore
    callvalue
    push1 0x07
    sstore
    address
    push2 0x014a
    sstore
    origin
    push2 0x014c
    sstore
    calldatasize
    push2 0x0150
    sstore
    codesize
    push2 0x0152
    ... (5 more instructions)

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x02
    push20 0x62441cbe78aa4a4244e084d4f86098e31dced749
    push3 0x0493e0
    call
    push1 0x01
    sstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0x9073671d2bfb351331716fd279282eacf50824ad
    push3 0x055730
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
    ["tests/static/state_tests/stCallCodes/callcodecallcall_100Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcall_100(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> CALL -> CALL-> code, params check."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xdb43306b16c521b9cc3667fbe7d1b697bb1f9605")
    callee = Address("0x62441cbe78aa4a4244e084d4f86098e31dced749")
    callee_1 = Address("0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c")
    callee_2 = Address("0x9073671d2bfb351331716fd279282eacf50824ad")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.PUSH20[0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c]
        + Op.PUSH3[0x3d090] + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x4]
        + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x7] + Op.SSTORE + Op.ADDRESS
        + Op.PUSH2[0x14a] + Op.SSTORE + Op.ORIGIN + Op.PUSH2[0x14c] + Op.SSTORE
        + Op.CALLDATASIZE + Op.PUSH2[0x150] + Op.SSTORE + Op.CODESIZE
        + Op.PUSH2[0x152] + Op.SSTORE + Op.GASPRICE + Op.PUSH2[0x154] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x2] + Op.PUSH20[0x62441cbe78aa4a4244e084d4f86098e31dced749]
        + Op.PUSH3[0x493e0] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x9073671d2bfb351331716fd279282eacf50824ad]
        + Op.PUSH3[0x55730] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
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
