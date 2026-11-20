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
recipient. The nonexistent recipient is also covered without a state gas
reservoir.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def recipients(fork: Fork) -> list:
    """
    Return the recipient kinds, with the state gas reservoir choice.

    Only the nonexistent recipient is created, which costs state gas on forks
    with the state gas reservoir; there it is covered both paying from the
    reservoir (implicit gas limit above the cap) and from regular gas
    (`state_gas_reservoir=0` pins the gas limit to the cap).
    """
    cases = [
        pytest.param("nonexistent", None, id="nonexistent"),
        pytest.param("funded_eoa", None, id="funded_eoa"),
        pytest.param("eoa_with_storage", None, id="eoa_with_storage"),
    ]
    if fork.state_gas_reservoir_enabled():
        cases.append(
            pytest.param("nonexistent", 0, id="nonexistent_no_reservoir")
        )
    return cases


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
@pytest.mark.valid_from("Frontier")
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
@pytest.mark.parametrize_by_fork("recipient, state_gas_reservoir", recipients)
def test_non_zero_value_transaction_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    data: Bytes,
    recipient: str,
    state_gas_reservoir: int | None,
) -> None:
    """Send a value-1 transaction carrying `data` to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        to = pre.nonexistent_account()
        expected = Account(storage={}, balance=TX_VALUE)
    elif recipient == "funded_eoa":
        to = pre.fund_eoa(amount=1)
        expected = Account(balance_change=TX_VALUE)
    else:
        storage[0] = 1
        to = pre.fund_eoa(amount=1, storage=storage)
        expected = Account(storage=storage, balance_change=TX_VALUE)

    # Leave the reservoir unset unless the case pins it to zero.
    reservoir_kwargs = (
        {}
        if state_gas_reservoir is None
        else {"state_gas_reservoir": state_gas_reservoir}
    )
    tx = Transaction(
        sender=sender,
        to=to,
        data=data,
        value=TX_VALUE,
        protected=fork.supports_protected_txs(),
        **reservoir_kwargs,
    )

    post = {to: expected}

    state_test(pre=pre, post=post, tx=tx)
