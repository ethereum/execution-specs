"""
Test_return1.

Ported from:
state_tests/stSystemOperationsTest/return1Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/return1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_return1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE8 0 55) (RETURN 0 2)}
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2)
        + Op.STOP,
        balance=23,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
