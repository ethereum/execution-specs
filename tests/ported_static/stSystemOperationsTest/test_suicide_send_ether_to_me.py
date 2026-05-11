"""
Test_suicide_send_ether_to_me.

Ported from:
state_tests/stSystemOperationsTest/suicideSendEtherToMeFiller.json
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
    ["state_tests/stSystemOperationsTest/suicideSendEtherToMeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_send_ether_to_me(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_send_ether_to_me."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (SELFDESTRUCT (ADDRESS) )}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        sender: Account(balance=0xDE0B6B3A75E81AC, nonce=1),
        target: Account(storage={}, balance=0xDE0B6B3A76586A0, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
