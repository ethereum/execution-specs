"""
Test SELFDESTRUCT beneficiaries from a called contract.

Ported from:
state_tests/VMTests/vmTests/suicideFiller.yml

@manually-enhanced: Do not overwrite. Fork-derived gas used receipt check.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
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
    fork: Fork,
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
    victim_code = (
        Op.SELFDESTRUCT(
            address=target,
            address_warm=beneficiary != "random",
            account_new=beneficiary == "random",
        )
        + Op.STOP
    )
    victim = pre.deploy_contract(code=victim_code, balance=VICTIM_BALANCE)
    caller_code = Op.SSTORE(0, Op.CALL(address=victim)) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    gas_used = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.gas_cost(fork)
        + victim_code.gas_cost(fork)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )
    post: dict = {}
    if beneficiary == "myself":
        post[caller] = Account(storage={0: 1}, balance_change=0)
        post[victim] = Account(balance_change=0, code=victim_code)
    elif beneficiary == "caller":
        post[caller] = Account(storage={0: 1}, balance_change=VICTIM_BALANCE)
        post[victim] = Account(balance=0, code=victim_code)
    else:
        post[caller] = Account(storage={0: 1}, balance_change=0)
        post[absent] = Account(balance_change=VICTIM_BALANCE)
        post[victim] = Account(balance=0, code=victim_code)
    state_test(pre=pre, post=post, tx=tx)
