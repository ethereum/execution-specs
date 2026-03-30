"""
Test_suicide_not_existing_account.

Ported from:
state_tests/stSystemOperationsTest/suicideNotExistingAccountFiller.json
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
    [
        "state_tests/stSystemOperationsTest/suicideNotExistingAccountFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_not_existing_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_not_existing_account."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (SELFDESTRUCT 0xaa1722f3947def4cf144679da39c4c32bdc35681 )}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xAA1722F3947DEF4CF144679DA39C4C32BDC35681
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x70C22830049F2678C8AA93D0060683CD67696495),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        Address(0xAA1722F3947DEF4CF144679DA39C4C32BDC35681): Account(
            balance=0xDE0B6B3A76586A0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
