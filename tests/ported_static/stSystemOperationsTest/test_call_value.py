"""
Test_call_value.

Ported from:
state_tests/stSystemOperationsTest/callValueFiller.json
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
    ["state_tests/stSystemOperationsTest/callValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_value."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { [[0]] (CALLVALUE) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CALLVALUE) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0x186A0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
