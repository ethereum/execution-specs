"""
Bug discovered on ropsten https://github.com/ethereum/go-ethereum/pull/2...

Ported from:
state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/transactionIntinsicBug_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
def test_transaction_intinsic_bug_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Reject a sender funded for the effective price but not the max fee."""
    gas_limit = 50_000
    priority_fee = 20
    value = 0x2DC6C14
    base_fee = Environment().set_fork_requirements(fork).base_fee_per_gas
    assert base_fee is not None
    sender_balance = gas_limit * (base_fee + priority_fee) + value
    sender = pre.fund_eoa(amount=sender_balance)

    tx = Transaction(
        sender=sender,
        to=pre.fund_eoa(),
        data=Bytes("00"),
        gas_limit=gas_limit,
        value=value,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=priority_fee,
        access_list=[],
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    post = {sender: Account(balance=sender_balance)}

    state_test(pre=pre, post=post, tx=tx)
