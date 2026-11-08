"""
Test_suicide_origin.

Ported from:
state_tests/stSystemOperationsTest/suicideOriginFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/suicideOriginFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_suicide_origin(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_origin."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[0]] (ORIGIN) (SELFDESTRUCT (ORIGIN))}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ORIGIN)
        + Op.SELFDESTRUCT(address=Op.ORIGIN)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={0: sender}, balance=0, nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
