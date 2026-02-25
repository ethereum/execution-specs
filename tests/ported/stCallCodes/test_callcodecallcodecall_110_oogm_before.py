"""
callcode -> callcode -> (oog) call -> code

Ported from:
tests/static/state_tests/stCallCodes/callcodecallcodecall_110_OOGMBeforeFiller.json

callee code:
    push3 0x2fffff
    push1 0x00
    sha3
    pop
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xb126c622075b1189fb6c45e851641cfaddf65b36
    push3 0x061a80
    call
    push1 0x02
    sstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x51a61d678ec27711369c527e5d42a9de66a5727f
    push3 0x0927c0
    callcode
    push1 0x01
    sstore
    push1 0x01
    push1 0x0b
    sstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x8e6e134402f2eeca8e910e8ec62b45b36ee31f30
    push3 0x0c3500
    callcode
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x01
    push1 0x03
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
    ["tests/static/state_tests/stCallCodes/callcodecallcodecall_110_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecall_110_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """callcode -> callcode -> (oog) call -> code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x9e57433afaff8a546fbc43cf0330afb6561dc550")
    callee = Address("0x51a61d678ec27711369c527e5d42a9de66a5727f")
    callee_1 = Address("0x8e6e134402f2eeca8e910e8ec62b45b36ee31f30")
    callee_2 = Address("0xb126c622075b1189fb6c45e851641cfaddf65b36")

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
        Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.POP + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb126c622075b1189fb6c45e851641cfaddf65b36] + Op.PUSH3[0x61a80]
        + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x51a61d678ec27711369c527e5d42a9de66a5727f]
        + Op.PUSH3[0x927c0] + Op.CALLCODE + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0xb] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x8e6e134402f2eeca8e910e8ec62b45b36ee31f30]
        + Op.PUSH3[0xc3500] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
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
