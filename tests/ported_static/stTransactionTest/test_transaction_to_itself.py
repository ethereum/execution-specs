"""
test_transaction_to_itself

Ported from:
state_tests/stTransactionTest/TransactionToItselfFiller.json
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
    ["state_tests/stTransactionTest/TransactionToItselfFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_to_itself(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_transaction_to_itself"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x3b9aca00)


    tx = Transaction(
        sender=sender,
        to=sender,
        data=b'',
        gas_limit=25000,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(balance=0x3b9795b0, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
