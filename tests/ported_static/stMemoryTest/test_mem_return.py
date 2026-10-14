"""
Test_mem_return.

Ported from:
state_tests/stMemoryTest/memReturnFiller.json
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
    ["state_tests/stMemoryTest/memReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_mem_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mem_return."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) (RETURN 0 (MSIZE))  }
    target = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.RETURN(offset=0x0, size=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "ff55883355001144bbccddffeeaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # noqa: E501
        ),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
