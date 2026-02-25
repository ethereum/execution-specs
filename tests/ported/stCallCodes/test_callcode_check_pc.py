"""
check the PC after doing call to a contract

Ported from:
tests/static/state_tests/stCallCodes/callcode_checkPCFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xfa7fc61138ee12431f8693335fb2bf5af4051632
    push3 0x0f4240
    call
    pop
    pc
    push1 0x03
    sstore
    stop

callee code:
    push1 0x01
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
    ["tests/static/state_tests/stCallCodes/callcode_checkPCFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_check_pc(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """check the PC after doing call to a contract."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x6861b8d2ba9a24e77f63623e4a5e83e2bc6a30df")
    callee = Address("0xfa7fc61138ee12431f8693335fb2bf5af4051632")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xfa7fc61138ee12431f8693335fb2bf5af4051632]
        + Op.PUSH3[0xf4240] + Op.CALL + Op.POP + Op.PC + Op.PUSH1[0x3] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=1100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
