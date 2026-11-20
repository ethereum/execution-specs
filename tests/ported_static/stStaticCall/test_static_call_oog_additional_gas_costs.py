"""
STATICCALL an account from a transaction too short on gas for the
caller's stores.

Ported from:
state_tests/stStaticCall/static_call_OOG_additionalGasCosts1Filler.json
state_tests/stStaticCall/static_call_OOG_additionalGasCosts2_ParisFiller.json

@manually-enhanced: Do not overwrite. Merged on the callee's kind.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_GAS = 30_000
CALL_GAS = 6000
CALLEE_BALANCE = 10


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_call_OOG_additionalGasCosts1Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_call_OOG_additionalGasCosts2_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "callee_exists",
    [
        pytest.param(False, id="nonexistent"),
        pytest.param(True, id="funded_eoa"),
    ],
)
def test_static_call_oog_additional_gas_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    callee_exists: bool,
) -> None:
    """
    Verify the transaction runs out of gas and reverts the caller's
    stores, whether the STATICCALL target exists or not.
    """
    callee: Address
    if callee_exists:
        callee = pre.fund_eoa(amount=CALLEE_BALANCE)
    else:
        callee = pre.nonexistent_account()
    target = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            Op.STATICCALL(
                gas=CALL_GAS, address=callee, args_size=64, ret_size=64
            ),
        )
        + Op.SSTORE(1, Op.GAS)
        + Op.STOP,
    )
    sender = pre.fund_eoa()

    tx = Transaction(sender=sender, to=target, gas_limit=TX_GAS)

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        callee: (
            Account(balance=CALLEE_BALANCE)
            if callee_exists
            else Account.NONEXISTENT
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
