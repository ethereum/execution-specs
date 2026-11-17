"""
Reject a transaction whose sender account has code.

Ported from:
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsFiller.yml
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsItselfFiller.yml
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml
state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml

@manually-enhanced: Do not overwrite. Merged the sender-with-code cases.
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsFiller.yml",  # noqa: E501
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_callsItselfFiller.yml",  # noqa: E501
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_init_ParisFiller.yml",  # noqa: E501
        "state_tests/stEIP3607/transactionCollidingWithNonEmptyAccount_send_ParisFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("to", ["contract", "self", "eoa", "create"])
def test_transaction_from_account_with_code(
    state_test: StateTestFiller,
    pre: Alloc,
    to: str,
) -> None:
    """Send a call, self-call, transfer or creation from a sender with code."""
    sender = pre.fund_eoa(code=Op.SSTORE(1, 0))

    destination: Address | None
    if to == "contract":
        destination = pre.deploy_contract(code=Op.SSTORE(1, 0))
    elif to == "self":
        destination = sender
    elif to == "eoa":
        destination = pre.fund_eoa(amount=10)
    elif to == "create":
        destination = None
    else:
        raise ValueError(f"Unknown destination: {to}")

    tx = Transaction(
        sender=sender,
        to=destination,
        value=100_000,
        error=TransactionException.SENDER_NOT_EOA,
    )
    state_test(pre=pre, post={}, tx=tx)
