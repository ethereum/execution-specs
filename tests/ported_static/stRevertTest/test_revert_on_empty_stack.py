"""
Calling a runtime code that contains only a single `REVERT` should...

Ported from:
state_tests/stRevertTest/RevertOnEmptyStackFiller.json
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
    ["state_tests/stRevertTest/RevertOnEmptyStackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_revert_on_empty_stack(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calling a runtime code that contains only a single `REVERT` should..."""
    sender = pre.fund_eoa(amount=0x5AF3107A4000)

    # Source: raw
    # 0xfd
    target = pre.deploy_contract(
        code=Op.REVERT,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2000000,
    )

    post = {sender: Account(balance=0x5AF30F491300, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
