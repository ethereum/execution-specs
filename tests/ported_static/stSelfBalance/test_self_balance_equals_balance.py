"""
Test_self_balance_equals_balance.

Ported from:
state_tests/stSelfBalance/selfBalanceEqualsBalanceFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
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
@pytest.mark.pre_alloc_mutable
def test_self_balance_equals_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance_equals_balance."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: lll
    # { [[ 1 ]] (EQ (SELFBALANCE) (BALANCE (ADDRESS))) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.EQ(Op.SELFBALANCE, Op.BALANCE(address=Op.ADDRESS)),
        )
        + Op.STOP,
        balance=500,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
