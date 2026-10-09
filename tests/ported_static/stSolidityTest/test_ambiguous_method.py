"""
Test_ambiguous_method.

Ported from:
state_tests/stSolidityTest/AmbiguousMethodFiller.json
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
    ["state_tests/stSolidityTest/AmbiguousMethodFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_ambiguous_method(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_ambiguous_method."""
    sender = pre.fund_eoa(amount=0x12A05F200)

    # Source: raw
    # 0x60003560e060020a90048063c040622614601557005b601b6021565b60006000f35b61014f60008190555056  # noqa: E501
    target = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x15, condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x1B]
        + Op.JUMP(pc=0x21)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH2[0x14F]
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.JUMP,
        balance=0x186A0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=300000,
        value=1,
    )

    post = {target: Account(storage={0: 335})}

    state_test(pre=pre, post=post, tx=tx)
