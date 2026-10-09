"""
Test_mem32kb_minus_33.

Ported from:
state_tests/stMemoryTest/mem32kb-33Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/mem32kb-33Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_mem32kb_minus_33(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_mem32kb_minus_33."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (MSTORE 31935 42) [[ 1 ]] (MLOAD 31935) [[ 0 ]] (MSIZE) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x7CBF, value=0x2A)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x7CBF))
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=10,
    )

    post = {
        target: Account(storage={0: 31968, 1: 42}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
