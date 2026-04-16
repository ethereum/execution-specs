"""
Test_transaction_create_suicide_in_initcode.

Ported from:
state_tests/stInitCodeTest/TransactionCreateSuicideInInitcodeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/TransactionCreateSuicideInInitcodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_create_suicide_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction_create_suicide_in_initcode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
        gas_limit=155000,
        value=1,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
