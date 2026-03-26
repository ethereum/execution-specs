"""
test_non_zero_value_transaction_cal_lwith_data_to_empty_paris

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json
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
    ["state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALLwithData_ToEmpty_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_transaction_cal_lwith_data_to_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_non_zero_value_transaction_cal_lwith_data_to_empty_paris"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0x76fae819612a29489a1a43208613d8f8557b8898")  # noqa: E501
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    pre[addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=10)


    tx = Transaction(
        sender=sender,
        to=addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b,
        data=bytes.fromhex("1122334455667788991011121314151617181920"),
        gas_limit=600000,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(balance=11)}

    state_test(env=env, pre=pre, post=post, tx=tx)
