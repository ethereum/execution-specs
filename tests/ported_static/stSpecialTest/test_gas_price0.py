"""
Test_gas_price0.

Ported from:
state_tests/stSpecialTest/gasPrice0Filler.json
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
    ["state_tests/stSpecialTest/gasPrice0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_gas_price0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_gas_price0."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6001600101600055
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)),
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=656192,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 2})}

    state_test(pre=pre, post=post, tx=tx)
