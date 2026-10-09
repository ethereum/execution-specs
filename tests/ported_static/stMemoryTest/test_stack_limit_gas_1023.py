"""
Test_stack_limit_gas_1023.

Ported from:
state_tests/stMemoryTest/stackLimitGas_1023Filler.json
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
    ["state_tests/stMemoryTest/stackLimitGas_1023Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_stack_limit_gas_1023(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_stack_limit_gas_1023."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # (asm 1021 0x00 MSTORE JUMPDEST GAS 0x01 0x00 MLOAD SUB 0x00 MSTORE 0x00 MLOAD 0x06 JUMPI STOP )  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x3FD)
        + Op.JUMPDEST
        + Op.GAS
        + Op.MSTORE(offset=0x0, value=Op.SUB(Op.MLOAD(offset=0x0), 0x1))
        + Op.JUMPI(pc=0x6, condition=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
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
