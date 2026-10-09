"""
Test_mload_dejavu.

Ported from:
state_tests/stMemoryTest/mload_dejavuFiller.json
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
    ["state_tests/stMemoryTest/mload_dejavuFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_mload_dejavu(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mload_dejavu."""
    sender = pre.fund_eoa(amount=0x271000000000)

    # Source: raw
    # 0x630FFFFFFF51
    target = pre.deploy_contract(
        code=Op.MLOAD(offset=0xFFFFFFF),
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
