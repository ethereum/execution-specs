"""
Test_suicide_not_existing_account.

Ported from:
state_tests/stSystemOperationsTest/suicideNotExistingAccountFiller.json
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
        "state_tests/stSystemOperationsTest/suicideNotExistingAccountFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_suicide_not_existing_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_not_existing_account."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (SELFDESTRUCT 0xaa1722f3947def4cf144679da39c4c32bdc35681 )}
    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(
            address=0xAA1722F3947DEF4CF144679DA39C4C32BDC35681
        )
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

    post = {
        Address(0xAA1722F3947DEF4CF144679DA39C4C32BDC35681): Account(
            balance=0xDE0B6B3A76586A0
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
