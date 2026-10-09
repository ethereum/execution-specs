"""
Test_create_with_invalid_opcode.

Ported from:
state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json
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
    ["state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_create_with_invalid_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_with_invalid_opcode."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x444242424245434253f0
    target = pre.deploy_contract(
        code=Op.PREVRANDAO
        + Op.TIMESTAMP * 4
        + Op.GASLIMIT
        + Op.MSTORE8(offset=Op.TIMESTAMP, value=Op.NUMBER)
        + Op.CREATE,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=2)}

    state_test(pre=pre, post=post, tx=tx)
