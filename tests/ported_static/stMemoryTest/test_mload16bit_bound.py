"""
Test_mload16bit_bound.

Ported from:
state_tests/stMemoryTest/mload16bitBoundFiller.json
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
    ["state_tests/stMemoryTest/mload16bitBoundFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_mload16bit_bound(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mload16bit_bound."""
    sender = pre.fund_eoa(amount=0xA00050281798)

    # Source: lll
    # { [[ 1 ]] (MLOAD 65536) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x10000)) + Op.STOP,
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
