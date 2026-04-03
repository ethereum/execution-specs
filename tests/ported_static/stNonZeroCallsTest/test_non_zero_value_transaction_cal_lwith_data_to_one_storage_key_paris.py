"""
Test_non_zero_value_transaction_cal_lwith_data_to_one_storage_key_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json
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
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_transaction_cal_lwith_data_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_transaction_cal_lwith_data_to_one_storage_key_p..."""  # noqa: E501
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x4757608F18B70777AE788DD4056EEED52F7AA68F)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    pre[addr] = Account(balance=10, storage={0: 1})

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Address(0x1122334455667788991011121314151617181920),
        gas_limit=600000,
        value=1,
    )

    post = {addr: Account(storage={0: 1}, balance=11)}

    state_test(env=env, pre=pre, post=post, tx=tx)
