"""
Apparently this test was testing theoretical issue occur when tr gas >...

Ported from:
state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/OverflowGasMakeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_overflow_gas_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Apparently this test was testing theoretical issue occur when tr..."""
    sender = pre.fund_eoa(amount=0x4FEC000000000139C)

    tx = Transaction(
        sender=sender,
        to=pre.nonexistent_account(),
        data=Bytes(""),
        gas_limit=100000,
        value=501,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
