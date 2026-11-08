"""
Test_transaction_sending_to_zero.

Ported from:
state_tests/stTransactionTest/TransactionSendingToZeroFiller.json

@manually-enhanced: Do not overwrite. The tx sends value 1 to the empty
zero address, so EIP-2780 charges NEW_ACCOUNT state gas at the top frame;
with the default zero reservoir that charge spills into regular gas. The
`gas_limit` is lifted by `fork.transaction_top_frame_state_gas` for an
EMPTY_ACCOUNT recipient with `sends_value=True` (0 on pre-EIP-2780
forks), so the literal 25000 budget stays valid across the repricing. Do
not collapse the lift back to a hardcoded gas_limit.
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
    ["state_tests/stTransactionTest/TransactionSendingToZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_sending_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_sending_to_zero."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # EIP-2780 charges ``NEW_ACCOUNT`` state gas at the top frame when
    # value is sent to an empty recipient; with the default zero
    # state-gas reservoir that charge spills into regular gas, so lift
    # ``gas_limit`` by exactly that amount (0 on pre-EIP-2780 forks).
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    tx = Transaction(
        sender=sender,
        to=Address(0x0000000000000000000000000000000000000000),
        data=Bytes(""),
        gas_limit=25000 + top_frame_state_gas,
        value=1,
    )

    post = {
        Address(0x0000000000000000000000000000000000000000): Account(
            balance=1
        ),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
