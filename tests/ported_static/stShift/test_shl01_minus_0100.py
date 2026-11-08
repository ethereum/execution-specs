"""
Test_shl01_minus_0100.

Ported from:
state_tests/stShift/shl01-0100Filler.json
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
    ["state_tests/stShift/shl01-0100Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_shl01_minus_0100(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_shl01_minus_0100."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x60016101001b600055
    target_code = Op.SSTORE(key=0x0, value=Op.SHL(0x100, 0x1))
    target = pre.deploy_contract(
        code=target_code,
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
        target: Account(
            storage={0: 0},
            code=target_code,
            balance=0xDE0B6B3A76586A0,
        ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
