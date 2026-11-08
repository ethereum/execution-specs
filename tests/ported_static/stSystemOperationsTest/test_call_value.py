"""
Test_call_value.

Ported from:
state_tests/stSystemOperationsTest/callValueFiller.json
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
    ["state_tests/stSystemOperationsTest/callValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_value."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[0]] (CALLVALUE) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLVALUE) + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0x186A0})}

    state_test(pre=pre, post=post, tx=tx)
