"""
Test_returndatasize_initial.

Ported from:
state_tests/stReturnDataTest/returndatasize_initialFiller.json
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
    ["state_tests/stReturnDataTest/returndatasize_initialFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_returndatasize_initial(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_initial."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (SSTORE 0 (RETURNDATASIZE)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE) + Op.STOP,
        storage={0: 1},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)
