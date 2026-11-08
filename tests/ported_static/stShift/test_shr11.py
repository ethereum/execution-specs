"""
Taken from https://github.com/ethereum/EIPs/blob/master/EIPS/eip-145.md.

Ported from:
state_tests/stShift/shr11Filler.json
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
    ["state_tests/stShift/shr11Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_shr11(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Taken from https://github."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x600160011c600055
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHR(0x1, 0x1)),
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
