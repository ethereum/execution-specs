"""
Test_transaction_to_addressh160minus_one.

Ported from:
state_tests/stTransactionTest/TransactionToAddressh160minusOneFiller.json

@manually-enhanced: Do not overwrite. Sending value to the empty 0xff..ff
recipient triggers EIP-2780's NEW_ACCOUNT top-frame state-gas charge.
Both the tx and block ``gas_limit`` are lifted by
``fork.transaction_top_frame_state_gas(EMPTY_ACCOUNT, sends_value=True)``
so the charge (which spills into regular gas via the zero reservoir)
fits the budget; this derived value is 0 on pre-EIP-2780 forks, keeping
the original hardcoded 22000/100000 limits intact there.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    RecipientType,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransactionTest/TransactionToAddressh160minusOneFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_to_addressh160minus_one(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_to_addressh160minus_one."""
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    # EIP-2780 charges ``NEW_ACCOUNT`` state gas at the top frame when
    # value is sent to an empty recipient; with the default zero
    # state-gas reservoir that charge spills into regular gas, so lift
    # ``gas_limit`` by exactly that amount (0 on pre-EIP-2780 forks).
    # The block ``gas_limit`` must also accommodate the lifted tx.
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )

    tx = Transaction(
        sender=sender,
        to=Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        data=Bytes(""),
        gas_limit=22000 + top_frame_state_gas,
        value=100,
    )

    post = {
        Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF): Account(
            balance=100
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
