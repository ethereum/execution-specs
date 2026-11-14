"""
Test_refund_tx_to_suicide_oog.

Ported from:
state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json
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
    ["state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_refund_tx_to_suicide_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_tx_to_suicide_oog."""
    sender = pre.fund_eoa()

    # Source: lll
    # { (SELFDESTRUCT 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) }
    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=21002,
        value=10,
    )

    post = {
        sender: Account(balance_change=-GasFee(tx, gas=tx.gas_limit)),
        target: Account(storage={1: 1}, balance=0xDE0B6B3A7640000),
    }

    state_test(pre=pre, post=post, tx=tx)
