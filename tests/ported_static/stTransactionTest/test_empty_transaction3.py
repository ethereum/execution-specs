"""
Test_empty_transaction3.

Ported from:
state_tests/stTransactionTest/EmptyTransaction3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/EmptyTransaction3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_empty_transaction3(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_empty_transaction3."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(""),
        gas_limit=2055000 if fork >= Amsterdam else 55000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(code=b""),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
