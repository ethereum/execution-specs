"""
Self-destruct a contract from its own creation transaction init code.

Ported from:
state_tests/stInitCodeTest/TransactionCreateAutoSuicideContractFiller.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/TransactionCreateAutoSuicideContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_create_auto_suicide_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Self-destruct a contract from its own creation transaction."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    tx_value = 15

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SELFDESTRUCT(address=beneficiary),
        value=tx_value,
    )

    post = {
        sender: Account(nonce=1),
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        beneficiary: Account(balance=tx_value),
    }

    state_test(pre=pre, post=post, tx=tx)
