"""
Test_codesize_init.

Ported from:
state_tests/stCodeSizeLimit/codesizeInitFiller.json
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
    ["state_tests/stCodeSizeLimit/codesizeInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_codesize_init(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_codesize_init."""
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x1, value=Op.CODESIZE)
        + Op.SSTORE(key=0x2, value=Op.EXTCODESIZE(address=Op.ADDRESS))
        + Op.STOP,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={1: 10, 2: 0}, balance=0
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
