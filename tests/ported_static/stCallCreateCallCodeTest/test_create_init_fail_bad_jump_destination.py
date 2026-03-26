"""
create fails because init code has bad jump dest (underflow)

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFailBadJumpDestinationFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/createInitFailBadJumpDestinationFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_bad_jump_destination(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """create fails because init code has bad jump dest (underflow)"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # {(MSTORE8 0 0x56 ) (SELFDESTRUCT (CREATE 1 0 1)) }
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0x56)
        + Op.SELFDESTRUCT(address=Op.CREATE(value=0x1, offset=0x0, size=0x1))
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x866b704865d7d80842e1d7c2c1c8bf682a3a437c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=2200000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x0000000000000000000000000000000000000000"): Account(balance=0xde0b6b3a76586a0),  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
