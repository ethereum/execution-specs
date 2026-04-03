"""
Test_gas_price0.

Ported from:
state_tests/stSpecialTest/gasPrice0Filler.json
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
    ["state_tests/stSpecialTest/gasPrice0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_gas_price0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_gas_price0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x6001600101600055
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xBCC1197CCD23A97607F2F96D031F3432E0D16A02),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=656192,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 2})}

    state_test(env=env, pre=pre, post=post, tx=tx)
