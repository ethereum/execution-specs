"""
Push expect 32 bytes. but we have only 10 byte.

Ported from:
state_tests/stSpecialTest/push32withoutByteFiller.json
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
    ["state_tests/stSpecialTest/push32withoutByteFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_push32without_byte(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Push expect 32 bytes."""
    sender = pre.fund_eoa(amount=0x8AC7230489E80000, nonce=1)

    # Source: raw
    # 0x7f11223344556677889910
    target = pre.deploy_contract(
        code=bytes.fromhex("7f11223344556677889910"),
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=500000,
        nonce=1,
    )

    post = {sender: Account(nonce=2)}

    state_test(pre=pre, post=post, tx=tx)
