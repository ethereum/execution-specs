"""
Push expect 32 bytes. but we have only 10 byte.

Ported from:
state_tests/stSpecialTest/push32withoutByteFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/push32withoutByteFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_push32without_byte(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Push expect 32 bytes."""
    sender = pre.fund_eoa()

    # Source: raw
    # 0x7f11223344556677889910
    target = pre.deploy_contract(
        code=Op.PUSH32 + bytes.fromhex("11223344556677889910"),
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=500000,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
