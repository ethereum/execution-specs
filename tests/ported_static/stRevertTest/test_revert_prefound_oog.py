"""
Test_revert_prefound_oog.

Ported from:
state_tests/stRevertTest/RevertPrefoundOOGFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_revert_prefound_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_oog."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    addr = pre.fund_eoa(amount=1)
    # Source: lll
    # { [[0]] (CREATE 0 0 32) (KECCAK256 0x00 0x2fffff) }
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x0, offset=0x0, size=0x20)
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        balance=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=930000,
    )

    post = {addr: Account(storage={}, code=b"", balance=1, nonce=0)}

    state_test(pre=pre, post=post, tx=tx)
