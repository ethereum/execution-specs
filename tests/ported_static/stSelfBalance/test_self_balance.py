"""
Test_self_balance.

Ported from:
state_tests/stSelfBalance/selfBalanceFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stSelfBalance/selfBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: lll
    # { [[ 1 ]] (SELFBALANCE) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.SELFBALANCE) + Op.STOP,
        balance=500,
        nonce=0,
        address=Address(0xC4686D898FAA85A20D23378B84956C9E10295DB5),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={1: 500})}

    state_test(env=env, pre=pre, post=post, tx=tx)
