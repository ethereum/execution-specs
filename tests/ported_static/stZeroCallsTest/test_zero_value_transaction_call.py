"""
Zero-value transaction, with and without data, to different kinds of
recipient.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithDataFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. Eight fillers parametrized by data and
recipient.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALLFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithDataFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "recipient",
    [
        "nonexistent",
        "funded_eoa",
        "eoa_with_storage",
    ],
)
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(Bytes(), id="no_data"),
        pytest.param(
            Bytes("0x1122334455667788991011121314151617181920"),
            id="with_data",
        ),
    ],
)
def test_zero_value_transaction_call(
    state_test: StateTestFiller,
    pre: Alloc,
    data: Bytes,
    recipient: str,
) -> None:
    """Send a zero-value transaction carrying `data` to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        to = pre.nonexistent_account()
        expected = Account.NONEXISTENT
    elif recipient == "funded_eoa":
        to = pre.fund_eoa(amount=1)
        expected = Account(balance_change=0)
    else:
        storage[0] = 1
        to = pre.fund_eoa(amount=1, storage=storage)
        expected = Account(storage=storage, balance_change=0)

    tx = Transaction(sender=sender, to=to, data=data)

    post = {
        sender: Account(nonce=1),
        to: expected,
    }

    state_test(pre=pre, post=post, tx=tx)
