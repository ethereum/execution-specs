"""
Test_non_zero_value_transaction_cal_lwith_data.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithDataFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithDataFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_non_zero_value_transaction_cal_lwith_data(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_transaction_cal_lwith_data."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        data=Address(0x1122334455667788991011121314151617181920),
        gas_limit=600000,
        value=1,
    )

    post = {
        Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B): Account(
            storage={}, balance=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
