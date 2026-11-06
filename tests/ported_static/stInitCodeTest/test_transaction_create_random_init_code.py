"""
Stack underflow in init code.

Ported from:
state_tests/stInitCodeTest/TransactionCreateRandomInitCodeFiller.json
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
    ["state_tests/stInitCodeTest/TransactionCreateRandomInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_transaction_create_random_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Stack underflow in init code."""
    sender = pre.fund_eoa(amount=0x2540BE400)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.CALLCODE
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2
        + Op.STOP,
        value=1,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
