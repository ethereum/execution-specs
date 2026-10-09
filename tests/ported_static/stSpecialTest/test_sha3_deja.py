"""
Test_sha3_deja.

Ported from:
state_tests/stSpecialTest/sha3_dejaFiller.json
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
    ["state_tests/stSpecialTest/sha3_dejaFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_sha3_deja(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_sha3_deja."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6042601f53600064ffffffffff2080
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x1F, value=0x42)
        + Op.SHA3(offset=0xFFFFFFFFFF, size=0x0)
        + Op.DUP1,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
