"""
A state test with invalid transaction example filler.

Ported from:
state_tests/stExample/invalidTrFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stExample/invalidTrFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
def test_invalid_tr(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A state test with invalid transaction example filler."""
    sender = pre.fund_eoa()

    # Source: lll
    # { [[0]] (ADD 1 1) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=1000,
        value=0x186A0,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    post = {
        target: Account(storage={0: 0}),
        sender: Account(nonce=0),
    }

    state_test(pre=pre, post=post, tx=tx)
