"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stZeroCallsTest
ZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_transaction_cal_lwith_data_to_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )
    contract = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("1122334455667788991011121314151617181920"),
        gas_limit=600000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stZeroCallsTest/ZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_zero_value_transaction_cal_lwith_data_to_empty_paris_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )
    contract = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("1122334455667788991011121314151617181920"),
        gas_limit=600000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
