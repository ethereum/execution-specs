"""
Create fails because init code has stack underflow, trying to suicide...

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFailStackUnderflowFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createInitFailStackUnderflowFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_init_fail_stack_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has stack underflow, trying to..."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {(MSTORE8 0 0x01 ) (SELFDESTRUCT (CREATE 1 0 1)) }
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0x1)
        + Op.SELFDESTRUCT(address=Op.CREATE(value=0x1, offset=0x0, size=0x1))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2200000,
        value=0x186A0,
    )

    post = {
        Address(0x0000000000000000000000000000000000000000): Account(
            balance=0xDE0B6B3A76586A0
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
