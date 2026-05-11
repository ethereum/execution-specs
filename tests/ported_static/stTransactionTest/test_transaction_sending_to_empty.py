"""
Test_transaction_sending_to_empty.

Ported from:
state_tests/stTransactionTest/TransactionSendingToEmptyFiller.json
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
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/TransactionSendingToEmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_sending_to_empty(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction_sending_to_empty."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x5F5E100)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(""),
        gas_limit=53000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(code=b""),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
