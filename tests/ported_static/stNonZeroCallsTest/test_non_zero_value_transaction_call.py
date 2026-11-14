"""
Value-1 transaction, with and without data, to different kinds of recipient.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToNonNonZeroBalanceFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithDataFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToNonNonZeroBalanceFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json

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

TX_VALUE = 1


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToNonNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithDataFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToNonNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "recipient",
    [
        "nonexistent",
        "funded_eoa",
        pytest.param("eoa_with_storage", marks=pytest.mark.pre_alloc_mutable),
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
def test_non_zero_value_transaction_call(
    state_test: StateTestFiller,
    pre: Alloc,
    data: Bytes,
    recipient: str,
) -> None:
    """Send a value-1 transaction carrying `data` to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        to = pre.nonexistent_account()
        expected = Account(storage={}, balance=TX_VALUE)
    elif recipient == "funded_eoa":
        to = pre.fund_eoa()
        expected = Account(balance_change=TX_VALUE)
    else:
        storage[0] = 1
        to = pre.fund_eoa(storage=storage, nonce=0)
        expected = Account(storage=storage, balance_change=TX_VALUE)

    tx = Transaction(sender=sender, to=to, data=data, value=TX_VALUE)

    post = {to: expected}

    state_test(pre=pre, post=post, tx=tx)
