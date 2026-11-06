"""
Test SELFDESTRUCT beneficiaries from a called contract.

Ported from:
state_tests/VMTests/vmTests/suicideFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

VICTIM_BALANCE = 0xFF000000000000


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/suicideFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("beneficiary", ["caller", "random", "myself"])
def test_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    beneficiary: str,
) -> None:
    """Send the balance of a called contract to its SELFDESTRUCT target."""
    absent = pre.nonexistent_account()
    target: Address | Bytecode
    if beneficiary == "caller":
        target = Op.CALLER
    elif beneficiary == "random":
        target = absent
    elif beneficiary == "myself":
        target = Op.ADDRESS
    else:
        raise ValueError(f"Unknown beneficiary: {beneficiary}")
    victim_code = Op.SELFDESTRUCT(address=target) + Op.STOP
    victim = pre.deploy_contract(code=victim_code, balance=VICTIM_BALANCE)
    caller = pre.deploy_contract(code=Op.CALL(address=victim) + Op.STOP)

    tx = Transaction(sender=pre.fund_eoa(), to=caller)
    post: dict = {}
    if beneficiary == "myself":
        post[caller] = Account(balance_change=0)
        post[victim] = Account(balance_change=0, code=victim_code)
    else:
        received = caller if beneficiary == "caller" else absent
        post[received] = Account(balance_change=VICTIM_BALANCE)
        post[victim] = Account(balance=0, code=victim_code)
    state_test(pre=pre, post=post, tx=tx)
