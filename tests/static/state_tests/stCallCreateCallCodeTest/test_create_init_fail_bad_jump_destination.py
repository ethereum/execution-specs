"""
create fails because init code has bad jump dest (underflow)

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/createInitFailBadJumpDestinationFiller.json

contract code:
    push1 0x56
    push1 0x00
    mstore8
    push1 0x01
    push1 0x00
    push1 0x01
    create
    selfdestruct
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/createInitFailBadJumpDestinationFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_bad_jump_destination(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """create fails because init code has bad jump dest (underflow)."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x866b704865d7d80842e1d7c2c1c8bf682a3a437c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x56] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.CREATE + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=2200000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
