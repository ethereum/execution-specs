"""
Test_transaction_to_itself.

Ported from:
state_tests/stTransactionTest/TransactionToItselfFiller.json
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
    ["state_tests/stTransactionTest/TransactionToItselfFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_to_itself(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction_to_itself."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=sender,
        data=Bytes(""),
        gas_limit=25000,
        value=1,
    )

    post = {sender: Account(balance=0x3B9795B0, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
