"""
Test_call10.

Ported from:
state_tests/stSystemOperationsTest/Call10Filler.json
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
    ["state_tests/stSystemOperationsTest/Call10Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call10(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call10."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    addr = pre.fund_eoa(amount=7000)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 10) [i](+ @i 1) [[ 0 ]](CALL 0xfffffffffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 50000 0 0) ) [[ 1 ]] @i}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x42, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xA))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xFFFFFFFFFFF,
                address=Op.PUSH20[addr],
                value=0x1,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=1000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        value=10,
    )

    post = {target: Account(storage={0: 1, 1: 10})}

    state_test(pre=pre, post=post, tx=tx)
