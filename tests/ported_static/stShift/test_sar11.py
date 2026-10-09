"""
Test_sar11.

Ported from:
state_tests/stShift/sar11Filler.json
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
    ["state_tests/stShift/sar11Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_sar11(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_sar11."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x600160011d600055
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SAR(0x1, 0x1)),
        storage={0: 3},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        target: Account(storage={0: 0}, balance=0xDE0B6B3A76586A0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
