"""
Execution stops at SELFDESTRUCT; the CALL after it never runs.

Ported from:
state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALLEE_BENEFICIARY = Address(0x1)


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_suicides_stop_after_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Self-destruct to a self-destructing contract, then call it."""
    sender = pre.fund_eoa()
    callee = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=CALLEE_BENEFICIARY) + Op.STOP,
        balance=1110,
    )
    caller_code = (
        Op.SELFDESTRUCT(address=callee)
        + Op.CALL(gas=0x7530, address=callee)
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code, balance=10000)

    tx = Transaction(sender=sender, to=caller, value=10)

    post = {
        callee: Account(balance=1110 + 10000 + 10),
        caller: Account(code=caller_code, balance=0),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
