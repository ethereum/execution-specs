"""
Test_caller_account_balance.

Ported from:
state_tests/stSystemOperationsTest/callerAccountBalanceFiller.json
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
    ["state_tests/stSystemOperationsTest/callerAccountBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_caller_account_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_caller_account_balance."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[0]] (balance (caller)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.BALANCE(address=Op.CALLER)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0xDE0B6B3A16C9860})}

    state_test(pre=pre, post=post, tx=tx)
