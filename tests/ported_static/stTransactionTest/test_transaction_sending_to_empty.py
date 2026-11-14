"""
Test_transaction_sending_to_empty.

Ported from:
state_tests/stTransactionTest/TransactionSendingToEmptyFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/TransactionSendingToEmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_sending_to_empty(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_transaction_sending_to_empty."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=2053000 if fork >= Amsterdam else 53000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(code=b""),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
