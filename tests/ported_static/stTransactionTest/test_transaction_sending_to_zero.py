"""
Test_transaction_sending_to_zero.

Ported from:
state_tests/stTransactionTest/TransactionSendingToZeroFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stTransactionTest/TransactionSendingToZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_sending_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction_sending_to_zero."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=Address(0x0000000000000000000000000000000000000000),
        data=Bytes(""),
        gas_limit=25000,
        value=1,
    )

    post = {
        Address(0x0000000000000000000000000000000000000000): Account(
            balance=1
        ),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
