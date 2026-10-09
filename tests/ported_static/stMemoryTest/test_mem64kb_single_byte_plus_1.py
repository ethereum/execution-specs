"""
Test_mem64kb_single_byte_plus_1.

Ported from:
state_tests/stMemoryTest/mem64kb_singleByte+1Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
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
    ["state_tests/stMemoryTest/mem64kb_singleByte+1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_mem64kb_single_byte_plus_1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mem64kb_single_byte_plus_1."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (MSTORE8 64000 42) [[ 0 ]] (MSIZE) }
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0xFA00, value=0x2A)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(sender=sender, to=target, data=Bytes(""), value=10)

    post = {
        target: Account(storage={0: 64032}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
