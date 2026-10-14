"""
Test_self_balance_equals_balance.

Ported from:
state_tests/stSelfBalance/selfBalanceEqualsBalanceFiller.json
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
    ["state_tests/stSelfBalance/selfBalanceEqualsBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_self_balance_equals_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance_equals_balance."""
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    # Source: lll
    # { [[ 1 ]] (EQ (SELFBALANCE) (BALANCE (ADDRESS))) }
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.EQ(Op.SELFBALANCE, Op.BALANCE(address=Op.ADDRESS)),
        )
        + Op.STOP,
        balance=500,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
    )

    post = {target: Account(storage={1: 1})}

    state_test(pre=pre, post=post, tx=tx)
