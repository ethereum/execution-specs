"""
Test_refund_oog.

Ported from:
state_tests/stRefundTest/refund_OOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_refund_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_oog."""
    sender = pre.fund_eoa()

    # Source: lll
    # { [[ 1 ]] 0 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=26005,
        value=10,
    )

    post = {
        target: Account(storage={1: 1}, balance_change=0),
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
    }

    state_test(pre=pre, post=post, tx=tx)
