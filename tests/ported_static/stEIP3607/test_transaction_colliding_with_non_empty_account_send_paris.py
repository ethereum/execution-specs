"""
Account with non-empty code attempts to send tx to another account with...

Ported from:
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_transaction_colliding_with_non_empty_account_send_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Account with non-empty code attempts to send tx to another account..."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    coinbase = pre.fund_eoa(amount=0)
    addr = pre.fund_eoa(amount=10)

    tx = Transaction(
        sender=sender,
        to=addr,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
        error=TransactionException.SENDER_NOT_EOA,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
