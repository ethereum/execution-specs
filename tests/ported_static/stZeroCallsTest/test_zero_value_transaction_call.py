"""
Test_zero_value_transaction_call.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_zero_value_transaction_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_transaction_call."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        Address(
            0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
        ): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
