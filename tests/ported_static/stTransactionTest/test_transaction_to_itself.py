"""
Test_transaction_to_itself.

Ported from:
state_tests/stTransactionTest/TransactionToItselfFiller.json

@manually-enhanced: Do not overwrite. The sender pays only the
self-transfer intrinsic gas, derived from the fork calculator.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasFee,
    RecipientType,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/TransactionToItselfFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_to_itself(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_to_itself."""
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=sender,
        gas_limit=25000,
        value=1,
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.SELF,
        sends_value=True,
    )
    post = {
        sender: Account(balance_change=-GasFee(tx, gas=intrinsic), nonce=1)
    }

    state_test(pre=pre, post=post, tx=tx)
