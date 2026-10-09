"""
Test_eip2315_not_removed.

Ported from:
state_tests/stBadOpcode/eip2315NotRemovedFiller.json
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
    ["state_tests/stBadOpcode/eip2315NotRemovedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_eip2315_not_removed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_eip2315_not_removed."""
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFF)

    # Source: raw
    # 0x60045e005c60016000555d
    target = pre.deploy_contract(
        code=Op.PUSH1[0x4]
        + Op.MCOPY
        + Op.STOP
        + Op.TLOAD
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.TSTORE,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
    )

    post = {target: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)
