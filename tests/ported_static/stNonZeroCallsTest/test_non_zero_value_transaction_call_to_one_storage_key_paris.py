"""
Test_non_zero_value_transaction_call_to_one_storage_key_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json
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
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_transaction_call_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_transaction_call_to_one_storage_key_paris."""
    addr = Address(0x4757608F18B70777AE788DD4056EEED52F7AA68F)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    pre[addr] = Account(balance=10, storage={0: 1})

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Bytes(""),
        gas_limit=600000,
        value=1,
    )

    post = {addr: Account(storage={0: 1}, balance=11)}

    state_test(pre=pre, post=post, tx=tx)
