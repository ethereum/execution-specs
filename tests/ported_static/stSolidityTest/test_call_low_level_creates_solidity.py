"""
Create a contract that calls back into its creator.

Ported from:
state_tests/stSolidityTest/CallLowLevelCreatesSolidityFiller.json

@manually-enhanced: Do not overwrite. The self address comes from
ADDRESS, padded to keep the jump and CODECOPY offsets.
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
    ["state_tests/stSolidityTest/CallLowLevelCreatesSolidityFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_low_level_creates_solidity(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_low_level_creates_solidity."""
    sender = pre.fund_eoa()

    target = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x21], condition=Op.EQ(0x30DEBB42, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x32], condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x2C]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=Op.PUSH2[0xC7])
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH2[0x3A]
        + Op.JUMP(pc=Op.PUSH2[0x44])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        # Self address, padded to the filler's PUSH20 width.
        + Op.ADDRESS
        + Op.PUSH18[0x0]
        + Op.POP
        + Op.PUSH1[0x1]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xD2], size=0x6A)
        + Op.CREATE(value=0x0, offset=0x0, size=0x6A)
        + Op.SWAP1
        + Op.POP
        + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        + Op.PUSH4[0x19AB453C]
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(
            offset=Op.DUP2,
            value=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x1)),
        )
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=Op.PUSH2[0xBC], condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.SLOAD(key=0x0)
        + Op.SWAP2
        + Op.POP * 2
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP * 2
        + Op.JUMP
        + Op.STOP
        + Op.PUSH1[0x5E]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x15, condition=Op.EQ(0x19AB453C, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x1E]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=0x24)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        + Op.PUSH4[0x30DEBB42]
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(offset=Op.DUP2, value=0xE1)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=0x59, condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 3
        + Op.JUMP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        value=1,
    )

    post = {target: Account(storage={0: 225, 1: target}, nonce=2)}

    state_test(pre=pre, post=post, tx=tx)
