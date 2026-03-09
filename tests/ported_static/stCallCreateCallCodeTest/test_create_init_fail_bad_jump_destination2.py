"""
create fails because init code has bad jump dest.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
createInitFailBadJumpDestination2Filler.json
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
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/createInitFailBadJumpDestination2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_bad_jump_destination2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has bad jump dest."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: LLL
    # {(MSTORE 0 0x61ffff56 ) (SELFDESTRUCT (CREATE 1 28 4)) }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x61FFFF56)
            + Op.SELFDESTRUCT(
                address=Op.CREATE(value=0x1, offset=0x1C, size=0x4)
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x9cc12364004e761c5c594f6dce3787cff273029c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=2200000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
