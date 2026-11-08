"""
Test_suicide_address.

Ported from:
state_tests/stSystemOperationsTest/suicideAddressFiller.json
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
    ["state_tests/stSystemOperationsTest/suicideAddressFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_suicide_address(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_address."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[0]] (ADDRESS) (SELFDESTRUCT (ADDRESS))}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADDRESS)
        + Op.SELFDESTRUCT(address=Op.ADDRESS)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {target: Account(balance=0xDE0B6B3A76586A0)}

    state_test(pre=pre, post=post, tx=tx)
