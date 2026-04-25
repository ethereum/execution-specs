"""
Test_non_zero_value_transaction_call_to_non_non_zero_balance.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToNonNonZeroBalanceFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_TransactionCALL_ToNonNonZeroBalanceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_non_zero_value_transaction_call_to_non_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_transaction_call_to_non_non_zero_balance."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=100)  # noqa: F841

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Bytes(""),
        gas_limit=600000,
        value=1,
    )

    post = {addr: Account(balance=101)}

    state_test(env=env, pre=pre, post=post, tx=tx)
