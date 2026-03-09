"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/block504980Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/block504980Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_block504980(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x1cdc8315bdb1362de8b7b2fa9ee75dc873037179")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3141592,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    # Source: raw bytecode
    callee_5 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x289F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xC9AE5868651BF7B7DB6E360217DB49CE4E69C07E,
            )
            + Op.JUMPI(
                pc=0x127, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC4982A85))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0xA0, value=Op.SLOAD(key=Op.SHA3))
            + Op.MLOAD(offset=0xA0)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0xE0]
            + Op.MSTORE
            + Op.MSTORE(offset=0x140, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x10B,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x140), Op.MLOAD(offset=0xA0)),
                ),
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x140)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0xE0),
                    Op.MUL(0x20, Op.MLOAD(offset=0x140)),
                ),
                value=Op.SLOAD(key=Op.SHA3),
            )
            + Op.MSTORE(
                offset=0x140, value=Op.ADD(Op.MLOAD(offset=0x140), 0x1)
            )
            + Op.JUMP(pc=Op.PUSH2[0xAD])
            + Op.JUMPDEST
            + Op.MLOAD(offset=0xE0)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x176, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xCC1C944E))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x1A0, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x1A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1D5, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x95A405B9))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x1E0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x1E0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x200, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x200, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x224, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x71EBB662))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x240, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x240, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x325, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7A57A3DB))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x280, value=Op.CALLDATALOAD(offset=0x44))
            + Op.PUSH1[0xC0]
            + Op.PUSH1[0xC0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x3)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x280)
            )
            + Op.MSTORE(offset=Op.ADD(0xA0, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2E9,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2C8)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x394, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xF73DC690))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x3C0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x3E0, value=Op.CALLDATALOAD(offset=0x64))
            + Op.PUSH1[0xC0]
            + Op.PUSH1[0xC0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x3)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x3C0)
            )
            + Op.MSTORE(
                offset=Op.ADD(0xA0, Op.DUP2), value=Op.MLOAD(offset=0x3E0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x400, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x400, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x3F3, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x54CC6109))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x3C0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x3C0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x440, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x440, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x442, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC63EF546))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x480, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x480, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x533, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x9381779B))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x6)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4F7,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x4D6)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x624, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x4F9C6EEB))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x7)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x5E8,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x5C7)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x715, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7DC12195))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x8)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6D9,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x6B8)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x806, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xFA9832D1))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x9)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x7CA,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x7A9)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x8F7, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2C5A40D5))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xA)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x8BB,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x89A)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x9EB, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xE05DCB56))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xB)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x2]
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.ADD
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x9AF,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x98E)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xA3A, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x586B5BE0))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xC)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0xB80, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0xB80, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xB58, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xEB8AF5AA))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xD)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.MUL(0x20, Op.SDIV)
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xB1C,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0xAFB)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xC76, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7AB6EA8A))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xE)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.MUL(0x20, Op.SDIV)
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xC3A,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0xC19)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xD94, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2B810CB9))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xF)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.MUL(0x20, Op.SDIV)
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xD58,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0xD37)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xE85, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7FB42E46))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x10)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xE49,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0xE28)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xF76, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x734FA727))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x11)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xF3A,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0xF19)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1067, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC67FA857))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x12)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x102B,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x100A)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1185, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x5ED853E4))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x13)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.MUL(0x20, Op.SDIV)
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1149,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1128)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x12A3, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB86F5125))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x14)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.MUL(0x20, Op.SDIV)
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1267,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1246)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1394, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xBC3D7D85))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x15)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MUL(0x20, Op.SLOAD(key=Op.SHA3))
            + Op.DUP1
            + Op.ADD(0x20, Op.DUP1)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1358,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DIV(Op.DUP4, 0x20))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.SLOAD(key=Op.ADD(Op.DUP5, Op.DUP1)),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1337)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2)),
                value=Op.AND(
                    Op.SLOAD(key=Op.ADD(Op.DUP6, Op.DUP2)),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1481, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xA2302F2F))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x1680, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x16A0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0x16A0)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x1680),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x1680),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.SLOAD(key=Op.SHA3)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x1680),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x1680),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x1740, value=0x1)
            + Op.RETURN(offset=0x1740, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x14DD, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x58CA2BC))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x1760, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0x1760)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x17A0, value=0x1)
            + Op.RETURN(offset=0x17A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1617, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x5D3B965B))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x280, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(
                offset=0x17E0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x64)
                ),
            )
            + Op.MSTORE(offset=0x1800, value=Op.CALLDATALOAD(offset=0x84))
            + Op.POP
            + Op.PUSH1[0xC0]
            + Op.PUSH1[0xC0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x3)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x280)
            )
            + Op.MSTORE(offset=Op.ADD(0xA0, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x17E0), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x158C, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x17E0), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x156B)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x17E0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=0x1800)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x1900, value=0x1)
            + Op.RETURN(offset=0x1900, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1673, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB0E14F0F))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x1920, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0x1920)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x1960, value=0x1)
            + Op.RETURN(offset=0x1960, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1739, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x6ACCCDBC))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1980,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x6)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1980), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x170B, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1980), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x16EA)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1980),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1A40, value=0x1)
            + Op.RETURN(offset=0x1A40, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x17FF, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xA1FA51F9))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1A60,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x7)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1A60), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x17D1, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1A60), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x17B0)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1A60),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1B20, value=0x1)
            + Op.RETURN(offset=0x1B20, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x18C5, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xCD87F43A))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1B40,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x8)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1B40), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1897, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1B40), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1876)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1B40),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1C00, value=0x1)
            + Op.RETURN(offset=0x1C00, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x198B, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x222A8663))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1C20,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x9)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1C20), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x195D, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1C20), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x193C)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1C20),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1CE0, value=0x1)
            + Op.RETURN(offset=0x1CE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1A51, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB39E1FAA))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1D00,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xA)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1D00), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1A23, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1D00), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1A02)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1D00),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1DC0, value=0x1)
            + Op.RETURN(offset=0x1DC0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1B17, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xE365736B))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1DE0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xB)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1DE0), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1AE9, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1DE0), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1AC8)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1DE0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1EA0, value=0x1)
            + Op.RETURN(offset=0x1EA0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1B73, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xAAD7D6E3))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x1EC0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0x1EC0)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xC)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x1F00, value=0x1)
            + Op.RETURN(offset=0x1F00, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C39, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x1112B27))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x1F20,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xD)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x1F20), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C0B, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x1F20), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1BEA)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x1F20),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x1FE0, value=0x1)
            + Op.RETURN(offset=0x1FE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1CFF, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xBDBB239B))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x2000,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xE)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x2000), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1CD1, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x2000), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1CB0)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x2000),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x20C0, value=0x1)
            + Op.RETURN(offset=0x20C0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1DC5, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x5A0CD48))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x20E0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0xF)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x20E0), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1D97, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x20E0), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1D76)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x20E0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x21A0, value=0x1)
            + Op.RETURN(offset=0x21A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1E8B, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xAAA1FE35))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x21C0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x10)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x21C0), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1E5D, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x21C0), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1E3C)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x21C0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x2280, value=0x1)
            + Op.RETURN(offset=0x2280, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1F51, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2BE4935D))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x22A0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x11)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x22A0), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1F23, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x22A0), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F02)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x22A0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x2360, value=0x1)
            + Op.RETURN(offset=0x2360, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2017, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x13A8350D))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x2380,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x12)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x2380), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FE9, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x2380), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1FC8)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x2380),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x2440, value=0x1)
            + Op.RETURN(offset=0x2440, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x20DD, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xCB540B45))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x2460,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x13)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x2460), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x20AF, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x2460), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x208E)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x2460),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x2520, value=0x1)
            + Op.RETURN(offset=0x2520, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x21A3, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xBE030627))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x2540,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x14)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x2540), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2175, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x2540), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2154)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x2540),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x2600, value=0x1)
            + Op.RETURN(offset=0x2600, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2269, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x83FD77F0))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(
                offset=0x2620,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x15)
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x2620), 0x20))
            )
            + Op.DIV(Op.DUP2, 0x20)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x223B, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP2))
            )
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x2620), Op.MUL(0x20, Op.DUP1)
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x221A)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(Op.DUP3, Op.DUP5),
                value=Op.AND(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x2620),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.SUB(
                        0x0,
                        Op.EXP(0x100, Op.SUB(0x20, Op.MOD(Op.DUP4, 0x20))),
                    ),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x26E0, value=0x1)
            + Op.RETURN(offset=0x26E0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x22D5, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x59462205))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x3C0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x2700, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MLOAD(offset=0x2700)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.MLOAD(offset=0x3C0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x2740, value=0x1)
            + Op.RETURN(offset=0x2740, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2448, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xBB8E4196))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x2760, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x2780, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x27A0, value=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.SUB(Op.MLOAD(offset=0x2760), 0x1),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(
                pc=0x243B,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x27A0), Op.SLOAD(key=Op.SHA3)),
                ),
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.SUB(Op.MLOAD(offset=0x2760), 0x1),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2),
                value=Op.MLOAD(offset=0x27A0),
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x2780),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x2780),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(0x80, Op.DUP2), value=Op.SLOAD(key=Op.SHA3)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x2780),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2),
                value=Op.MLOAD(offset=0x2780),
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(
                offset=0x27A0, value=Op.ADD(Op.MLOAD(offset=0x27A0), 0x1)
            )
            + Op.JUMP(pc=0x22FC)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x2880, value=0x1)
            + Op.RETURN(offset=0x2880, size=0x20)
            + Op.JUMPDEST
            + Op.POP
        ),
        storage={
            0x65D5EFDFCC0FBA693DC9E467F633097FFDC97401901463AD0E28855486D1EDF: 0xB9D69098A6ACFE0C6411BCAAF430F78D363A9ADC32B78BC2E15CCD6E883E9784,  # noqa: E501
            0x12643FF300762717D27EFB567B82C65560D7B43249D908504E5510863AB82AAC: 0x154CF60E137C594516A065149610B6A3989396A42581D5FD8919E711C55DA225,  # noqa: E501
            0x1489023D18C5D10427C4AA8DC726E840EB5AE7F604A8E9243C61634FB009E4D7: 0x5,  # noqa: E501
            0x1489023D18C5D10427C4AA8DC726E840EB5AE7F604A8E9243C61634FB009E4D8: 0x1,  # noqa: E501
            0x19EFB13D6576359514ACE5211988A8D51379FA88CCD2B886B409F842B13D7932: 0xC849CC595B452D11C206D2EB8CDFA06DE211E3FF19EE0E0276DC857C05D4FE,  # noqa: E501
            0x1B37E91BF8580C7C6BCF8CDFF25C7ED78180124A94AF6F30C40D476A3D079AD6: 0xABA4CD295118A482A0A62579E35E4BA5BDD76146CC9E4D96172FCE8BE8977AB4,  # noqa: E501
            0x2BF9FD8FACDD6FD9C84657F5AD7381A5AECF670CDA68CB3C5829B6532C865506: 0x53098A1D111586DBCC0D051846284F5803C63C313E7F7E6D84430435D11D4C50,  # noqa: E501
            0x3111BFD25728C0ADFAD0F8C1AD79CB1B91167267DECA98DE88F156ED25CAEEDC: 0xAD393086F30B49511B08FDD27AC78810B084C7CD7DE6AC354F614C18EA9E7DF4,  # noqa: E501
            0x3379E7AE125C5C5D623D1D993C1459B61D6723B1C30D1AA026C48F6A6155B8EA: 0x8C4183732567A99A8A718E363391E102532F9A640E42968CF2354D9ACC908BB0,  # noqa: E501
            0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE2: 0x1,  # noqa: E501
            0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE3: 0x1,  # noqa: E501
            0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE4: 0x1,  # noqa: E501
            0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE5: 0x1,  # noqa: E501
            0x39050607FE892059A6344AB0F594F382FB0B345CAB373497246DBE86FE7E14E7: 0x2B3BCA833E482737E7E47B1568E6F890F8E1666490D38FE130ABD6F0CCB109CF,  # noqa: E501
            0x417BE8BC6791807372E0222A350BB8A5D67BBC8D7595C301D8A5A8372CFDCEF1: 0xABD4971B4605A7155802F70E08298B1CEB0E4E4EACCCCD348F77A77227F73A7F,  # noqa: E501
            0x41E9A54B3EE0C276AA076BABB161DE12B0F8916B47F8F6FB85CC387CF34696DD: 0x22F2F444EBDA9D2913FFEF5059B039EC9B5876AA71821991C2515BF79F64935E,  # noqa: E501
            0x45CEB8DA6FB8936592D3BCE4883F1A6A34D636F559E0A1070A5802A65AC39BD5: 0x57A5122FF3BF737B0DE0F9F08011A8648C19E43FF071FB7086234723C9383F1F,  # noqa: E501
            0x4AA6B934608A45C8F53A945C05DDEE1814A3B9F63A048FC7AD3D47E67156F024: 0xD03862BECEDADA67B4825A0238F3E67495CCB595CD7D08F1BD5D3160644B9299,  # noqa: E501
            0x4B8B58F0B0E326A5907D1A810E5FF31E05B4CAB45125B776DB8577E7DBC46BCE: 0x2F0000000000000000,  # noqa: E501
            0x4C33460347337BFC7DF08BF182988301B7B426A27A67F1C6C634F637C60E87AC: 0xBAB4AB2AD4EAFE7C84EF6A8CD69157D9CE6B843793A2CD0877B8E91F63CB2D4D,  # noqa: E501
            0x58DA0C0C256BBA101CE36FAD8BF838717A57E6AB850A191DC9C09DA9CE56BF1B: 0x5,  # noqa: E501
            0x5CB38B16DB1D632086D4AF695DE7F5F242A6E40947067F96EDD566FE2AC438EF: 0x6D0BE832B2007EA28CDA705B73922CBF9794C5A25B89BD2F28B7347ED2B96C86,  # noqa: E501
            0x64A9621CC4BA92BF738C55010C609DFAA3972A1138C30B5ADCEF1BA2363B360E: 0xD7953BFE8CB591F129FD0862A9E9C421151E2B5831560FF5215D23F751364B35,  # noqa: E501
            0x696664A5F0AB5ACD9304A377FB684F2D3FE6BB60B8A95CB2BDBB57DB767E7A84: 0x154CF60E137C594516A065149610B6A3989396A42581D5FD8919E711C55DA225,  # noqa: E501
            0x69AD1D19E617936ABDF05133BF268DC8CED6B518F22B249B5860967D07006487: 0x8C803B48B383DDABD1B3AFE858EFB48C203229B7317DD76149DDDAB4253B858A,  # noqa: E501
            0x70B3BF53996FAC325EB67608A4EEB0CD0B55DEF6255D7ED42AD28EC07238B5D6: 0x45E9723E9232B37207ECAC1C97B8647D053625A578D450F7456280B2FF8EFC27,  # noqa: E501
            0x7A9DCEE62E3E02CC8E020F372DF2EFDEB835F091C1EF1DBE221072D1095AABD2: 0x2F0000000000000000,  # noqa: E501
            0x7E4D8C0F6D8ABB4CE1AE45B254046ACEEDABFA9548851B8B5D3E2C0637C985FD: 0xB,  # noqa: E501
            0x7E95F3CC3315D289C52253BAABA29B1B00C86816E6B788D50795279A8BAA00DB: 0x45E9723E9232B37207ECAC1C97B8647D053625A578D450F7456280B2FF8EFC27,  # noqa: E501
            0x8DA187157087529EE4E9C381F8E3149C56ACF3BDFDA29B8B9B4532F24B83F5FE: 0x8C4183732567A99A8A718E363391E102532F9A640E42968CF2354D9ACC908BB0,  # noqa: E501
            0x9001F91DDAEF87BC067886E874C0749998C9B58B2EC8472CA014CA8B55F88578: 0xFB76974EEFCA01F33FB38646C2D3C1536F1A763D7AFF53AB7F877D4C5EA7FD0,  # noqa: E501
            0x9ED0CEDD2A9A78D949F40019F53D10031AEF6ED342C97E01FC03B481EE56B3CB: 0x4,  # noqa: E501
            0x9FDDF1DB29CAA5C1239EDD86E9E0835CDFE41F7253EC78F62D3DA8558D6F3CD7: 0x104EEF8FA35BF39F677D81855BC0B9F42317F32792E98E95E4DF441DEB634211,  # noqa: E501
            0xA0953566119395C11186B334805FC1A16175ECAC0ECC93AE0322264F0DC2E40D: 0x10C5A00466AB7C0ADAE1E93537CC275EA8CF23FF509D5466A1FD6F56B0A61D1B,  # noqa: E501
            0xAA0DBF8241EF3AE07C254E6869E84895BA2BE0779A7F261C8308A3114BE1C54A: 0x4,  # noqa: E501
            0xAFFE808B495D13A14391CE5F27C211C36DA12826969CD7841EE0D81E5B900E2D: 0x1,  # noqa: E501
            0xAFFE808B495D13A14391CE5F27C211C36DA12826969CD7841EE0D81E5B900E2E: 0x1,  # noqa: E501
            0xB4A2B68C48EF78AEB641EE538FAD51781022FD23ED9D93D211017DB6A02376CE: 0xFBC06642245CF2FED7ED46EA0A18A7185830B6F2C4E0A4CA55246041E8BFA72,  # noqa: E501
            0xBA8D79990898383919E437F2458B93B340072C89D963808D9E04F51858E3C5EC: 0x41D2CAC534D90A0DBD199117481A63E32CC11411DAB2EAA36C91C0EEC62823CF,  # noqa: E501
            0xBB3BC1A2015123750DF57D4CEFF7E28CB847910B79B34841DE905B59A8BB177C: 0x734417EB19E1873427257F1EA1594748C16CFA866A7B7CF896E281F2EC774A40,  # noqa: E501
            0xBF30CDCB83AB2BD5F5EEE691FFA4107B58B75BA6A5C2E6754D4C5C0437F2876C: 0x5,  # noqa: E501
            0xC2A26B80067FC36B8268B0D5B31AFFF953FA91CEBEA39F191E2763D6E71259B9: 0x2A43C547FE8DE2400D2A141016550E8BAE058D41164247C099E787DDD40E789,  # noqa: E501
            0xC98339D275EEF16E0562CA8521212CEF61AA0F39B12E2A27502AAA97A9E5E70F: 0x5A3DE2A5C268CDB75F4B01507AA80C4E4A1BC67BCB0DF265BBB00060774E5978,  # noqa: E501
            0xCBD6AE6BD61BC9270EC836F1919B3268113ABE076C7FEBFDB8CF573B199CE9A9: 0xF402B17773C1F7534034EE58DC0D2A3421470A7A67DAF4FA790DC3B420EEF790,  # noqa: E501
            0xD2C8CBB562FCCD0C9A3D0D491B7F65CC6A89856498F933427D9D21B745B9D50E: 0x3625A26FDB7B747501F1EE2500F98C49D9CD290383A21254587C3C49D2805321,  # noqa: E501
            0xD66F52A4E24585238CCC03443B2FDB8B2B100259BC7260F39097C7C339211FFE: 0x1641851904381915C86B60DF7E288896FB5F8EBAD65D594829FB9F2B59CD1DA6,  # noqa: E501
            0xD8F720C05A5526DD621D1831AE122ABDDD3DFECD8B63B0BA4C92FA7B2ADE44FF: 0xAD393086F30B49511B08FDD27AC78810B084C7CD7DE6AC354F614C18EA9E7DF4,  # noqa: E501
            0xDC22D3171B82817C910BBEAC1F8B50C8DE99F8C524F172AEF3491981BD5ED4FB: 0x94B8CBA4EA090D1C392FBC94B82FB9EF9F468A15BBC537F4D051776F4D422B1D,  # noqa: E501
            0xDCE8ADBDEFA929DBE60245F359446DB4174C62824B42E5D4D9E7B834B4D61DEB: 0x2C9069845B2E74C577FF1CD18DF6BC452805F527A9EE91FD4A059E0408B5DEA6,  # noqa: E501
            0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D196: 0x1,  # noqa: E501
            0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D197: 0x1,  # noqa: E501
            0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D198: 0x1,  # noqa: E501
            0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D199: 0x1,  # noqa: E501
            0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D19A: 0x1,  # noqa: E501
            0xE54F074C81BFA60B5BF413934C108086298B77291560EDFEEAD8AA1232E95236: 0xF40AAA24323C9E6983CCFFAFEEBE4B426509B901E8C98B8A40D881804804E6B,  # noqa: E501
            0xE66C0F55F66C752EDF73027D45B7B1AE729AE15E1C67C362DBC6F25EDF8D76FF: 0x1,  # noqa: E501
            0xE983D899F807BBCB5881F2DDF875B2EBB5CB8A7A4E77A8C98A40AAAE6A468735: 0x6D0BE832B2007EA28CDA705B73922CBF9794C5A25B89BD2F28B7347ED2B96C86,  # noqa: E501
            0xED7D6E2D40FBD5046412FFAD1C45B63D87C6197182D6DBC66BB1E5C6E4DED5C7: 0xABA4CD295118A482A0A62579E35E4BA5BDD76146CC9E4D96172FCE8BE8977AB4,  # noqa: E501
            0xF043B5A1952847579F233706A8F130889A484D2DA3E574FDD5859F05AAF52111: 0x2,  # noqa: E501
            0xF40F4CFDACB62DD799F36B580349FAC1F4A4CAF8DD3383CC387C35ADB6574E21: 0x2F0000000000000000,  # noqa: E501
            0xF60FA6E25E9028A6DC6B26BBC1EADAE3DA157DF0D1D6F6628BC33CAD68A7E455: 0x2D7D00618C059EBE40593B9497C633E1AC6E161DADBD5BB734C2663CD3E8A8E1,  # noqa: E501
            0xFD280AC5182D5B2366122F38ACFA6DC471240FFDE9D5FEB985CE7A2325C960E7: 0x3,  # noqa: E501
        },
        nonce=0,
        address=Address("0x0ea65418d7bf32680f55572c943a94b590804998"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x31F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xC9AE5868651BF7B7DB6E360217DB49CE4E69C07E,
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xEA65418D7BF32680F55572C943A94B590804998,
            )
            + Op.JUMPI(
                pc=0x38D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x27138BFB))
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7A66D7CA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0xE0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0xE0)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC60409C6)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x120,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x120)
            + Op.SWAP1
            + Op.POP
            + Op.NUMBER
            + Op.MSTORE(offset=0x100, value=Op.SDIV)
            + Op.MSTORE(offset=0x140, value=0x0)
            + Op.MSTORE(offset=0x160, value=0x0)
            + Op.MSTORE(offset=0x180, value=0x0)
            + Op.JUMPI(
                pc=0x10A,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SLT(
                            Op.MLOAD(offset=0x100),
                            Op.ADD(Op.MLOAD(offset=0xA0), 0x2),
                        ),
                    ),
                ),
            )
            + Op.MSTORE(offset=0x140, value=0x1)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1A0, value=0x0)
            + Op.MSTORE(offset=0x1C0, value=Op.MLOAD(offset=0x100))
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x184,
                condition=Op.ISZERO(
                    Op.SLT(
                        Op.MLOAD(offset=0x1C0),
                        Op.ADD(Op.MLOAD(offset=0x100), 0x64),
                    ),
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xCC1C944E)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x40),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x1E0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x1E0)
            + Op.SWAP1
            + Op.POP
            + Op.MLOAD(offset=0x1A0)
            + Op.MSTORE(offset=0x1A0, value=Op.ADD)
            + Op.MSTORE(
                offset=0x1C0, value=Op.ADD(Op.MLOAD(offset=0x1C0), 0x1)
            )
            + Op.JUMP(pc=0x119)
            + Op.JUMPDEST
            + Op.PUSH1[0x5]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xCC1C944E)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xA0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x40),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x200,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x200)
            + Op.SWAP1
            + Op.POP
            + Op.SLT
            + Op.JUMPI(pc=0x1D3, condition=Op.ISZERO(Op.DUP1))
            + Op.DUP1
            + Op.JUMP(pc=0x1DB)
            + Op.JUMPDEST
            + Op.SLT(Op.MLOAD(offset=0x1A0), 0xA)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x1EB, condition=Op.ISZERO)
            + Op.MLOAD(offset=0x140)
            + Op.JUMP(pc=0x1EE)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x336, condition=Op.ISZERO)
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC5476EFE)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x240,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x240)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7265802D)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x260,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x260)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC286273A)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x280,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x280)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7A66D7CA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x2A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x2A0)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xBB8E4196)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x100)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x40),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x64,
                    ret_offset=0x2C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x2C0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0x343)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x160, value=0x1)
            + Op.MSTORE(offset=0x180, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x355, condition=Op.ISZERO(Op.MLOAD(offset=0x140)))
            + Op.MLOAD(offset=0x160)
            + Op.JUMP(pc=0x358)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x366, condition=Op.ISZERO)
            + Op.MLOAD(offset=0x180)
            + Op.JUMP(pc=0x369)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x37F, condition=Op.ISZERO)
            + Op.MSTORE(offset=0x2E0, value=0x1)
            + Op.RETURN(offset=0x2E0, size=0x20)
            + Op.JUMP(pc=0x38C)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x300, value=0x0)
            + Op.RETURN(offset=0x300, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0x142a6927cf0060133187ba8a8e74d641438f0c1c"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=1, nonce=0)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x5DF, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEA65418D7BF32680F55572C943A94B590804998,
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xE509E3A93BEB1EBA72F8CB8D25F93A85E2D54AFB,
            )
            + Op.MSTORE(
                offset=0x60,
                value=0xC9AE5868651BF7B7DB6E360217DB49CE4E69C07E,
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF1562E1C0D0BAA3EA746442BB7F11153FCF5CFDA,
            )
            + Op.JUMPI(
                pc=0x38D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x546FDEB3))
            )
            + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x84))
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(
                pc=0x250,
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.MLOAD(
                            offset=Op.ADD(
                                Op.DUP3,
                                Op.MUL(
                                    0x20, Op.ADD(Op.MLOAD(offset=0x100), 0x1)
                                ),
                            ),
                        ),
                        0x0,
                    ),
                ),
            )
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE365736B)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x2F300BEE)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=0x2)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x100)
            )
            + Op.DUP5
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x1FC,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x223,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x280,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x280)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x37D)
            + Op.JUMPDEST
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE365736B)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x2F300BEE)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4),
                value=Op.SUB(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.DUP6,
                            Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x100), 0x1)),
                        ),
                    ),
                    0x1,
                ),
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x100)
            )
            + Op.DUP5
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x32D,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x354,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x2C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x2C0)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x2E0, value=0x1)
            + Op.RETURN(offset=0x2E0, size=0x20)
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x764, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xDE9080C8))
            )
            + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x84))
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.DUP2
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x2C5A40D5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.MLOAD(offset=0x140)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MLOAD(offset=0x120)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4EE,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x120))),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x28C8B315)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP2)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x40),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x360,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x360)
            + Op.SWAP1
            + Op.POP
            + Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP2))
            + Op.MSTORE
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x493)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x20C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xA647A5B9)
            + Op.DUP5
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x4), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x148), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP4
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x24), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xC4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x168), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xE4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x188), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x64), value=Op.MLOAD(offset=0x120)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x84), value=Op.MLOAD(offset=0x100)
            )
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x5B5,
                condition=Op.CALL(
                    gas=0x22,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0xA4,
                    ret_offset=Op.DUP2,
                    ret_size=0xA4,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0xA4)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x148))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x5DC,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x168))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x604,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xC4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x188))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x62C,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xE4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.DUP8
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP7,
                    args_size=Op.DUP5,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE365736B)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.DUP5
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x6DF,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x706,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x3C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x3C0)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPI(
                pc=0x752,
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.MLOAD(
                            offset=Op.ADD(
                                Op.DUP5,
                                Op.MUL(0x20, Op.MLOAD(offset=0x100)),
                            ),
                        ),
                        0x0,
                    ),
                ),
            )
            + Op.MSTORE(offset=0x3E0, value=0x0)
            + Op.RETURN(offset=0x3E0, size=0x20)
            + Op.JUMP(pc=0x75F)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x400, value=0x1)
            + Op.RETURN(offset=0x400, size=0x20)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xA66, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x384CA8DD))
            )
            + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x84))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xFA9832D1)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.MLOAD(offset=0x100)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xAAD7D6E3)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x5B180229)
            + Op.DUP4
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x4), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0x64), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0xC8), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP5
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x24), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0x84), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0xE8), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x100)
            )
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x901,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0xC8))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x927,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0x64)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0xE8))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x94E,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0x84)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x440,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x440)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.ADD(Op.DUP3, 0x44)
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x64,
                    ret_offset=0x460,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x460)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x222A8663)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0xA07,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xA2E,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x480,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x480)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x4A0, value=0x1)
            + Op.RETURN(offset=0x4A0, size=0x20)
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xD4B, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xD5DC5AF1))
            )
            + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x84))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x2C5A40D5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.MLOAD(offset=0x140)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x1AC]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xF4CA7DC4)
            + Op.DUP4
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x4), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0x84), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x24), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x128), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x120)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x64), value=Op.MLOAD(offset=0x100)
            )
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0xBE7,
                condition=Op.CALL(
                    gas=0x1F,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x84,
                    ret_offset=Op.DUP2,
                    ret_size=0x84,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x84)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xC0E,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0x84)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x128))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xC36,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.MLOAD(offset=0x140)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP7,
                    args_size=Op.DUP5,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xB39E1FAA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0xCEC,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xD13,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x4C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x4C0)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x4E0, value=0x1)
            + Op.RETURN(offset=0x4E0, size=0x20)
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x114C, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x939AA8C))
            )
            + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x84))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.ADD(Op.MLOAD(offset=0x100), 0x2)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7DC12195)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.MLOAD(offset=0x140)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x586B5BE0)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x500,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x500)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xEB8AF5AA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.MLOAD(offset=0x120)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0xC0]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x26C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x232B2734)
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x4), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xC4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x188), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP6
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x24), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xE4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x1A8), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.DUP5
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0x104), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x1C8), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x84), value=Op.MLOAD(offset=0x120)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0xA4), value=Op.MLOAD(offset=0x100)
            )
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0xF96,
                condition=Op.CALL(
                    gas=0x25,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0xC4,
                    ret_offset=Op.DUP2,
                    ret_size=0xC4,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0xC4)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x188))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xFBD,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xC4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x1A8))
            + Op.DUP1
            + Op.JUMPI(
                pc=0xFE5,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xE4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x1C8))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x100E,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0x104)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.MLOAD(offset=0x120)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP7,
                    args_size=Op.DUP5,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x14C]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x1112B27)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0xC0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0xE0)
            )
            + Op.DUP3
            + Op.ADD(
                0x20, Op.MUL(0x20, Op.MLOAD(offset=Op.SUB(Op.DUP2, 0x20)))
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x44), value=Op.DUP4)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, 0xA4), value=Op.SUB(Op.DUP3, 0x20)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP5, 0x108), value=Op.DUP1)
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(0x4, Op.DUP2)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x10C4,
                condition=Op.CALL(
                    gas=0x1C,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=0x64,
                    ret_offset=Op.DUP2,
                    ret_size=0x64,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.ADD(Op.DUP2, 0x64)
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=Op.ADD(Op.DUP3, 0x108))
            + Op.DUP1
            + Op.JUMPI(
                pc=0x10EB,
                condition=Op.CALL(
                    gas=Op.ADD(0x12, Op.SDIV(Op.DUP8, 0xA)),
                    address=0x4,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=Op.ADD(Op.DUP8, 0xA4)),
                    args_size=Op.DUP3,
                    ret_offset=Op.DUP6,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.INVALID
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SWAP4
            + Op.POP
            + Op.POP
            + Op.SUB(Op.DUP4, Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x580,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x580)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPI(
                pc=0x113A,
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.MLOAD(
                            offset=Op.ADD(
                                Op.DUP6,
                                Op.MUL(
                                    0x20, Op.ADD(Op.MLOAD(offset=0x100), 0x1)
                                ),
                            ),
                        ),
                        0x0,
                    ),
                ),
            )
            + Op.MSTORE(offset=0x5A0, value=0x0)
            + Op.RETURN(offset=0x5A0, size=0x20)
            + Op.JUMP(pc=0x1147)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x5C0, value=0x1)
            + Op.RETURN(offset=0x5C0, size=0x20)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0x9761fecf88590592cf05ce545504d376d1693ab3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xD8D726B7177A800000)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x75F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.MSTORE(
                offset=0x20,
                value=0x1E147037F0A63DF228FE6E7AEF730F1EA31C8CE3,
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xEA65418D7BF32680F55572C943A94B590804998,
            )
            + Op.MSTORE(
                offset=0x60,
                value=0xE509E3A93BEB1EBA72F8CB8D25F93A85E2D54AFB,
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xC9AE5868651BF7B7DB6E360217DB49CE4E69C07E,
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x142A6927CF0060133187BA8A8E74D641438F0C1C,
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0xB163E767E4C1BA5AE88B2EE7594F3A3FEC2BB096,
            )
            + Op.MSTORE(
                offset=0xE0,
                value=0xBA7B277319128EF4C22635534D0F61DFFDAA13AB,
            )
            + Op.MSTORE(
                offset=0x100,
                value=0x9761FECF88590592CF05CE545504D376D1693AB3,
            )
            + Op.MSTORE(
                offset=0x120,
                value=0xF70BBC50F1468CECAE0761EF09386A87C1C696EA,
            )
            + Op.MSTORE(
                offset=0x140,
                value=0xA89D22F049AAA5BBFB5F1A1939FFF3AE7A26AE74,
            )
            + Op.MSTORE(
                offset=0x160,
                value=0x174827F7E53E8CE13B047ADCAC0EB3F2CB0C3285,
            )
            + Op.JUMPI(
                pc=0xA88, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x36A560BD))
            )
            + Op.MSTORE(offset=0x1A0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x27138BFB)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0xA0),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x1E0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x1E0)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x195, condition=Op.ISZERO(Op.ISZERO))
            + Op.MSTORE(offset=0x200, value=Op.SUB(0x0, 0x1))
            + Op.RETURN(offset=0x200, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7A66D7CA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x220,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x220)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xCC1C944E)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP2)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x280),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x260,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x260)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x80B5E7BD)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x60),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x2A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x2A0)
            + Op.SWAP1
            + Op.POP
            + Op.MUL(Op.DUP3, Op.DUP1)
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x18633576)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x300,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x300)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x36D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x9)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xAC44D71E)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x160),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x360,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x360)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x7265802D)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x380,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x380)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC5476EFE)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x3A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x3A0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x3C0, value=Op.ADD(Op.DUP6, 0x1))
            + Op.RETURN(offset=0x3C0, size=0x20)
            + Op.JUMP(pc=0xA3A)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x3CD, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x0)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xEF72638A)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0xC0),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x3E0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x3E0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA39)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x42D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x1)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xA63E976C)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0xE0),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x400,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x400)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA38)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x48D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x533EA0ED)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0xE0),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x420,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x420)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA37)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x850, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xE05DCB56)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.ADD(Op.DUP6, 0x2)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x280),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x44,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x3D905045)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x480,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x480)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x633, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x4)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x939AA8C)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP8)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP7)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP5)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x100),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x4E0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x4E0)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x4C0]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC286273A)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x500,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x500)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPI(
                pc=0x5E5,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x4C0), 0x1)),
            )
            + Op.MSTORE(offset=0x520, value=Op.DUP3)
            + Op.RETURN(offset=0x520, size=0x20)
            + Op.JUMP(pc=0x62E)
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xAAC2FFB5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x540,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x540)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x560, value=Op.ADD(Op.DUP4, 0x1))
            + Op.RETURN(offset=0x560, size=0x20)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x804)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x694, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x0)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x546FDEB3)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP8)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP7)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP5)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x100),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x580,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x580)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0x803)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x742, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x1)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xDE9080C8)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP9)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP8)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP7)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP6)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x100),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x5A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x5A0)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x732, condition=Op.ISZERO(Op.EQ))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x1CDA01EF)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x5C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x5C0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x5E0, value=Op.DUP3)
            + Op.RETURN(offset=0x5E0, size=0x20)
            + Op.JUMP(pc=0x802)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x7A3, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x384CA8DD)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP8)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP7)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP5)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x100),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x600,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x600)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0x801)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x800, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xD5DC5AF1)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP8)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP7)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP5)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x100),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x620,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x620)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x1CDA01EF)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x640,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x640)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x660, value=Op.DUP3)
            + Op.RETURN(offset=0x660, size=0x20)
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA36)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8B1, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x4)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xF6559853)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x120),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x680,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x680)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA35)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x912, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x5)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xD8E5473D)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x120),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x6A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x6A0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA34)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x973, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x6)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x90507EA)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x120),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x6C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x6C0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA33)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x9D4, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x5B911842)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x140),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x6E0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x6E0)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0xA32)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xA31, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x8)))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC4]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xABE22B84)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.DUP6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=Op.DUP5)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x64), value=Op.DUP4)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x84), value=Op.DUP3)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x140),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0xA4,
                    ret_offset=0x700,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x700)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xAAC2FFB5)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x1A0)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x80),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x720,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x720)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x740, value=Op.ADD(Op.DUP2, 0x1))
            + Op.RETURN(offset=0x740, size=0x20)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0xb03f030056db7d467d778326658bac0d1b35d8f7"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_8 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x83F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0x66],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7A66D7CA)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x60, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x60, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xA5],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC60409C6)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0xA0, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0xA0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xE4],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x18633576)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0xE0, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0xE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1BC, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB3903C8A))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x120, value=Op.SLOAD(key=Op.SHA3))
            + Op.MLOAD(offset=0x120)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x160]
            + Op.MSTORE
            + Op.MSTORE(offset=0x1C0, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x19F,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x1C0), Op.MLOAD(offset=0x120)),
                ),
            )
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x160),
                    Op.MUL(0x20, Op.MLOAD(offset=0x1C0)),
                ),
                value=Op.SLOAD(key=Op.SHA3),
            )
            + Op.MSTORE(
                offset=0x1C0, value=Op.ADD(Op.MLOAD(offset=0x1C0), 0x1)
            )
            + Op.JUMP(pc=0x147)
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x160)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FD, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x6824E0FB))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x220, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x220, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x23E, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3DB16BE3))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x6)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x260, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x260, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2E0, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC3387858))
            )
            + Op.MSTORE(offset=0x2A0, value=0x0)
            + Op.MSTORE(offset=0x2C0, value=Op.SLOAD(key=0x0))
            + Op.MLOAD(offset=0x2C0)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x2E0]
            + Op.MSTORE
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2C3,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x2A0), Op.MLOAD(offset=0x2C0)),
                ),
            )
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x2A0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x2E0),
                    Op.MUL(0x20, Op.MLOAD(offset=0x2A0)),
                ),
                value=Op.SLOAD(key=Op.SHA3),
            )
            + Op.MSTORE(
                offset=0x2A0, value=Op.ADD(Op.MLOAD(offset=0x2A0), 0x1)
            )
            + Op.JUMP(pc=0x27A)
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x2E0)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2FA, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x175C6322))
            )
            + Op.MSTORE(offset=0x380, value=Op.SLOAD(key=0x0))
            + Op.RETURN(offset=0x380, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x336, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xD861F2B4))
            )
            + Op.MSTORE(offset=0x3A0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x3A0)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x3C0, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x3C0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x44F, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB0DAB01F))
            )
            + Op.MSTORE(offset=0x400, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x420, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x440, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x460, value=Op.CALLDATALOAD(offset=0x64))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x400)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.JUMPI(pc=0x441, condition=Op.ISZERO(Op.EQ))
            + Op.MLOAD(offset=0x420)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x400)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x440)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x400)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x460)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x400)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x6)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x400)
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.SLOAD(key=0x0))
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.MSTORE(offset=0x520, value=0x1)
            + Op.RETURN(offset=0x520, size=0x20)
            + Op.JUMP(pc=0x44E)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x540, value=0x0)
            + Op.RETURN(offset=0x540, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B9, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xAAC2FFB5))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x5A0, value=0x1)
            + Op.RETURN(offset=0x5A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x507, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x7265802D))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x5C0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MLOAD(offset=0x5C0)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x600, value=0x1)
            + Op.RETURN(offset=0x600, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x571, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC5476EFE))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x660, value=0x1)
            + Op.RETURN(offset=0x660, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x63B, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC551E31E))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x680, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x120, value=Op.SLOAD(key=Op.SHA3))
            + Op.MLOAD(offset=0x680)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x120)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x5)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x720, value=0x1)
            + Op.RETURN(offset=0x720, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x67C, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3D905045))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x3)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x740, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x740, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6E6, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x1CDA01EF))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x3)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x3)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x7C0, value=0x1)
            + Op.RETURN(offset=0x7C0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x734, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xC286273A))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x7E0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MLOAD(offset=0x7E0)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x3)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x820, value=0x1)
            + Op.RETURN(offset=0x820, size=0x20)
            + Op.JUMPDEST
            + Op.POP
        ),
        storage={
            0x0: 0x1,
            0xA4470E9D0419DF71F6257FCDFD2C0A3BAD96A23F5AB414BC10AAF1A31A536A7: 0xB4876148229C22BD2291F1A4F5468C8C789B23639370C4D447F270BA341DBBEC,  # noqa: E501
            0x16EF4193A274568D283FF919C299729E07696D9ADA48187B81D68E12E7B962DE: 0xA103C04E7ECB9B3395F77C7B0CAD28E62C85F042DE4767CCC6C005E6F47F8D4,  # noqa: E501
            0x1F1866E966F321B84535705846689749D34D5DC02994613E2931973C605D9E93: 0xC723D0AA4A60529FE42277C8094AA19263AFF36650136EFC5EDFD0785D457634,  # noqa: E501
            0x252A4EC7133643FDDCDB22A86C415F78B2DD251F18D1EFCD6A44ACF590C4AE72: 0x9CAF94B82715869E71D3CEE986094EA612F0258570B7E5EF47B5D09E9515322B,  # noqa: E501
            0x41B451E8D86D28ADD758CBD3F48A18FD04B11A80288C1DC434A5BF2D8FB1CA64: 0xB602498F12A8B4AF3A1FCA357CEA6B19BCD163DFEC1D845364CE1395F7C21FA7,  # noqa: E501
            0x491D10658C1EC762152D8AD2D890AD59111B1EE7B4BC25736046923D3534D9A5: 0x629E,  # noqa: E501
            0x5B0E8552EFD72A845E47318ABBBEF9DC9FCDFE0D1A06CDA44494401301581511: 0xFBC98F4017AE5C20459DAADAA6BEE519B6DE871D3DBAA9AB3F34340FEF4CB643,  # noqa: E501
            0x5B672A107BA6FAB01CBDDF079042E9F6176A8E6F154584FC4DF4B15674C9456E: 0x1603DA41D610854D85536B37D000E5EB7CA09786C43F50E7441C0AFBFF1DE0A9,  # noqa: E501
            0x605B934BD26C9ECDF7029A7DC062D3A6B87338511CFF96E0C5F13DE9EEA3462E: 0xF0D24F3D0EDA573FC5D43E3D0680993C51293752CD6DE205040D3197F412F475,  # noqa: E501
            0x618355E25491DFE86175F9D9B3147E4D680AA561D98384E3621DC6A3088B0846: 0x6B2E6D2D5DEB27DFFEC973F23AF4CAF111E66D1397F467DBBEDF5AB2192FB6B6,  # noqa: E501
            0x65112936BEC0F1E84FDA6623FB54E12BAADC8A4A208C8C4EB3ED5E79CBD7E85F: 0xA59AC24E3E0663413D0F87516BA8FB44C6C3E14DA8EAABBDE80F8EE285F65934,  # noqa: E501
            0x687CB2122DE7BACF42B9CD380B04FF2A2CE92A0B63706A9A78263B3CE86F3313: 0x200000000000000,  # noqa: E501
            0x72A539B064C98D29A514EE55694225E05FB41FE63E5FE710E4536BD9BA3591B4: 0x338ECFE6C523ED1184918B19584D97DD1095ECAADC49C7BA9DA62B8B513026E0,  # noqa: E501
            0x7AEB0A0CE8882A12D853078382A2BC72F7A94AF6109F167DE37B36C0A7DEB828: 0x4C428400EA8A7BD7C46BA9895B508770EFA4551F0D793E1BEB1207DA01D9962F,  # noqa: E501
            0x7C8F4A98E086F64E28C75F54712B5D44BEC3C29B5C70519E8880D3046A5618DC: 0xAAFC1F2601752B114D722070F75539BFEC7FAF49F0D48A48D27862F0C3B09903,  # noqa: E501
            0x809C325F50ACF5787776E960985E72443B4330AD1E2F466557FFFEE16BA51D44: 0xB940A56E64B5B661D87919B8EF03640EC077A6D72DD0B524ADEDAA7DDC91FF7A,  # noqa: E501
            0x84E4A80D33C5D2ABD2B0A5AEC0FDC5EAEED90AB31DB556E404A81718EA286E39: 0x1C,  # noqa: E501
            0x877305412FA2486F563C457B744E5C8B1E4D0ECA73371DE5E771F2ABC263F4DC: 0x7088A36F67276D475AA62127CFDE9790CC802FDF3A54DF49461A25EB8BF15707,  # noqa: E501
            0x922A8F2FC1CBE67C8ACC6A8A720983C366D71D3E2E78E3048949EBC913EA611A: 0x50FB9F913CA102534BB0A8EB8EBF19C68DFD16FFE5E207BCC580084CD4ECD8B4,  # noqa: E501
            0x987CB9ECFD8CE499D9D0E9E6B7DA29617AA02774A34F4A8EA54442F44A1E1936: 0x5179F98F555F1E9F1D4A335D16F41154579A53E361E9859269B6FA74EA9C7D21,  # noqa: E501
            0xADA5013122D395BA3C54772283FB069B10426056EF8CA54750CB9BB552A59E7D: 0xF69B5,  # noqa: E501
            0xB16B117660F31197087F4D6FE50D3D4579152244956F753F9653CCF85F4B35C4: 0x830272E3BB35226B047244CBDC46F1B6B864A280461E7A592F70E0863F4F1D33,  # noqa: E501
            0xB1F1AAEDFB83C7755A2BFFC9E2557F1723F9ABE5642397963E76248C9209AF57: 0xE9BE955C5FBFCD846D7425EAEA05CE897786AEFAD99665342CBF30761B352526,  # noqa: E501
            0xB7BD50FDF7B043411C9AC33F0AF2CEBC69C393EB0B91F4976946F9C7B15AD0DA: 0xFCCCA0E7832BAE9AFE799A6D6177DC3869FA6C5B5105F8DF6F365DE5723820EC,  # noqa: E501
            0xBC96058EB03504EE6F5C0A9582F8720D99A6E9738B171499507FACFF0B2C0B5B: 0x9DB6A4F2766B51013B8D2F9038131D1BB4AF725D019D111D7E26FF96C023B23F,  # noqa: E501
            0xC186C4F377B7F13892ADE9656ACD1522AA1F8AC151AC4F62457B5073241D79FC: 0x7289738FEF00F1770EEB098DB9BD486C01AC12398D79CDF935514A128C585C51,  # noqa: E501
            0xCAE57AE3017972D63EFFD8EAE44F5054402C3E890D154B905ED6B5B533327FA9: 0xD2E4BF465E61993D13089B940A7C55017A5117D8E43E4115550A139E1D4B3E3A,  # noqa: E501
            0xCF569EE7BF3ACCC0F893DFFD04F1A757F373EFE80893EFF504FB3678F688EC1D: 0x3,  # noqa: E501
            0xD69B7284545A9F5275DF64CE94848DC954FCB8A8B525E7AC801517C12A75AF84: 0x4202995350ABAE303B43E564AA79121A30B5F1AEA31F69CD25E07DD3FA64DCE7,  # noqa: E501
            0xD8F6F90F51E657690EE28D1CC80D81BC1B89290065891FDD853D09CAAAF756AA: 0x1,  # noqa: E501
            0xDE72F8EED43CC2A5A3EAA51483D14B17DC92BB26C154AE184CEE4B4895011EDC: 0x47CE2B6FDB72C3FABB9C74F82C1E3E522BCD42E614FD85C208AC3C4C840CEA72,  # noqa: E501
            0xE0E687DDF317F3D2B209AE3884148EFF0F636E16827F82EDED14ADA8FC603009: 0xFA7C8939F9B033162CF8D75EA69671BB8A27041BD4CDC76594E61E99333CB041,  # noqa: E501
            0xE8CDA339D72A1A350B62F1E3FA52E254C395CC9FDD9F60ADB21C7633FBDAB531: 0x128C4FDF4801A30EAE99DD58F0F3FF5CA65F71B66A9AC0F38DD450FB24B4AAAA,  # noqa: E501
            0xEC5E7F54FA5E516E616B04F9D5A0EE433A80E09ED47D7E5269AFD76C05FF251E: 0x14,  # noqa: E501
            0xF9A3BF5F2CCB903EE1A7644113B794DB0260DE404FB8F11203E75A7FFF151618: 0xBD94773C0D85C68240AE8DFD53D9D33CD137509BFC5D3433381299DF768C8377,  # noqa: E501
        },
        nonce=0,
        address=Address("0xc9ae5868651bf7b7db6e360217db49ce4e69c07e"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_9 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0xB7F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xC9AE5868651BF7B7DB6E360217DB49CE4E69C07E,
            )
            + Op.JUMPI(
                pc=0x245, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x8D3D587))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x80, value=Op.SLOAD(key=Op.SHA3))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=Op.ORIGIN)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.JUMPI(pc=0x14E, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=Op.ORIGIN)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x80, value=Op.SLOAD(key=Op.SHA3))
            + Op.PUSH9[0x2F0000000000000000]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.ORIGIN
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMP(pc=0x238)
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=Op.ORIGIN)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH9[0x2F0000000000000000]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.ORIGIN
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1E0, value=0x1)
            + Op.RETURN(offset=0x1E0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x29D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x28C8B315))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x200, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x200)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x220, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x220, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x386, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x74AF23EC))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x260, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x260)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x200, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(
                pc=0x332,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x200), 0x0)),
            )
            + Op.MLOAD(offset=0x260)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x200)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ISZERO(Op.EQ)
            + Op.JUMP(pc=0x335)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x347, condition=Op.ISZERO)
            + Op.MSTORE(offset=0x2C0, value=0x0)
            + Op.RETURN(offset=0x2C0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x200)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x2E0, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x2E0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x3DC, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x84D646EE))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x320, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x320, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6F4, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xF4229427))
            )
            + Op.MSTORE(offset=0x260, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x24]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x175C6322)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x4,
                    ret_offset=0x3A0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x3A0)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x360]
            + Op.MSTORE
            + Op.JUMPI(pc=0x581, condition=Op.ISZERO(Op.MLOAD(offset=0x260)))
            + Op.MUL(0x2, Op.MLOAD(offset=0x360))
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x3C0]
            + Op.MSTORE
            + Op.MLOAD(offset=0x360)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x420]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x24]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC3387858)
            + Op.MLOAD(offset=0x360)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x4,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x420]
            + Op.MSTORE
            + Op.MSTORE(offset=0x4C0, value=0x0)
            + Op.MSTORE(offset=0x4E0, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x57C,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x4C0), Op.MLOAD(offset=0x360)),
                ),
            )
            + Op.MSTORE(
                offset=0x60,
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x420),
                        Op.MUL(0x20, Op.MLOAD(offset=0x4C0)),
                    ),
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x74AF23EC)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0x260)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.ADDRESS,
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x520,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x520)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x500]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x56C,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x500), 0x0))
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x3C0),
                    Op.MUL(0x20, Op.MLOAD(offset=0x4E0)),
                ),
                value=Op.MLOAD(offset=0x60),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x3C0),
                    Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x4E0), 0x1)),
                ),
                value=Op.MLOAD(offset=0x500),
            )
            + Op.MSTORE(
                offset=0x4E0, value=Op.ADD(Op.MLOAD(offset=0x4E0), 0x2)
            )
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x4C0, value=Op.ADD(Op.MLOAD(offset=0x4C0), 0x1)
            )
            + Op.JUMP(pc=0x4CE)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x6D7)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x260, value=Op.ORIGIN)
            + Op.MUL(0x2, Op.MLOAD(offset=0x360))
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x3C0]
            + Op.MSTORE
            + Op.MLOAD(offset=0x360)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x420]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x24]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC3387858)
            + Op.MLOAD(offset=0x360)
            + Op.ADD(Op.MUL(0x20, Op.DUP2), 0x40)
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x20),
                    value=0x0,
                    args_offset=Op.DUP6,
                    args_size=0x4,
                    ret_offset=Op.DUP2,
                    ret_size=Op.ADD(0x40, Op.MUL(0x20, Op.DUP2)),
                ),
            )
            + Op.ADD(Op.DUP2, 0x40)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x420]
            + Op.MSTORE
            + Op.MSTORE(offset=0x4C0, value=0x0)
            + Op.MSTORE(offset=0x4E0, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6D6,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x4C0), Op.MLOAD(offset=0x360)),
                ),
            )
            + Op.MSTORE(
                offset=0x60,
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x420),
                        Op.MUL(0x20, Op.MLOAD(offset=0x4C0)),
                    ),
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x74AF23EC)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x4), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0x260)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.ADDRESS,
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x5C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x5C0)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x500]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x6C6,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x500), 0x0))
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x3C0),
                    Op.MUL(0x20, Op.MLOAD(offset=0x4E0)),
                ),
                value=Op.MLOAD(offset=0x60),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x3C0),
                    Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x4E0), 0x1)),
                ),
                value=Op.MLOAD(offset=0x500),
            )
            + Op.MSTORE(
                offset=0x4E0, value=Op.ADD(Op.MLOAD(offset=0x4E0), 0x2)
            )
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x4C0, value=Op.ADD(Op.MLOAD(offset=0x4C0), 0x1)
            )
            + Op.JUMP(pc=0x628)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x3C0)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x735, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x80B5E7BD))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x600, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x600, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x786, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x156F1C32))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x640, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x640)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x660, value=Op.SLOAD(key=Op.SHA3))
            + Op.RETURN(offset=0x660, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x878, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xB3A24FC0))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(
                offset=0x6C0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x4)
                ),
            )
            + Op.MSTORE(offset=0x6E0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.POP
            + Op.ADD(
                Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x6C0), 0x20)), 0x2
            )
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x700]
            + Op.MSTORE
            + Op.MSTORE(offset=Op.MLOAD(offset=0x700), value=Op.ORIGIN)
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x700), 0x20),
                value=Op.MLOAD(offset=0x6E0),
            )
            + Op.MSTORE(offset=0x4C0, value=0x2)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x838,
                condition=Op.ISZERO(
                    Op.SLT(
                        Op.MLOAD(offset=0x4C0),
                        Op.ADD(
                            Op.MLOAD(
                                offset=Op.SUB(Op.MLOAD(offset=0x6C0), 0x20)
                            ),
                            0x2,
                        ),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x700),
                    Op.MUL(0x20, Op.MLOAD(offset=0x4C0)),
                ),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x6C0),
                        Op.MUL(0x20, Op.SUB(Op.MLOAD(offset=0x4C0), 0x2)),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x4C0, value=Op.ADD(Op.MLOAD(offset=0x4C0), 0x1)
            )
            + Op.JUMP(pc=0x7F6)
            + Op.JUMPDEST
            + Op.MUL(
                0x20, Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x700), 0x20))
            )
            + Op.PUSH1[0x20]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.POP(
                Op.CALL(
                    gas=Op.ADD(0x48, Op.DUP8),
                    address=0x2,
                    value=0x0,
                    args_offset=Op.MLOAD(offset=0x700),
                    args_size=Op.DUP4,
                    ret_offset=Op.DUP2,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=Op.DUP1)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x760]
            + Op.MSTORE
            + Op.MSTORE(offset=0x7C0, value=Op.MLOAD(offset=0x760))
            + Op.RETURN(offset=0x7C0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xA1C, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xE346F5FC))
            )
            + Op.MSTORE(offset=0x7E0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x800, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x4C0, value=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x7E0)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(
                pc=0x9E6,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x4C0), Op.SLOAD(key=Op.SHA3)),
                ),
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x7E0)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x4C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x840, value=Op.SLOAD(key=Op.SHA3))
            + Op.MLOAD(offset=0x840)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x800)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x4C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x7E0)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x4C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x800)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x4C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x4C0)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x800)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x840)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(
                offset=0x4C0, value=Op.ADD(Op.MLOAD(offset=0x4C0), 0x1)
            )
            + Op.JUMP(pc=0x899)
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x4C0)
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x800)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0x920, value=0x1)
            + Op.RETURN(offset=0x920, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xB54, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3FB57036))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x940, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x960, value=Op.SLOAD(key=Op.SHA3))
            + Op.MLOAD(offset=0x960)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x940)
            )
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x960)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x940)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x960)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0xA40, value=0x1)
            + Op.RETURN(offset=0xA40, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xBEB, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x12709A33))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0xA60, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0xA60)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0xAC0, value=0x1)
            + Op.RETURN(offset=0xAC0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xC82, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x3229CF6E))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0xA60, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0xA60)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0xB20, value=0x1)
            + Op.RETURN(offset=0xB20, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xCE5, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xA75F5C6A))
            )
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0xA60, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MLOAD(offset=0xA60)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x60)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MSTORE(offset=0xB60, value=0x1)
            + Op.RETURN(offset=0xB60, size=0x20)
            + Op.JUMPDEST
            + Op.POP
        ),
        storage={
            0xF299DBBE3A7A5D949FE794E9A47B3106699C8110FF986EB84921C183E69E7F0: 0x2F0000000000000000,  # noqa: E501
            0x1EDCD36F61CAE5DC6414157DFBADF9F11CA013AC763E27F8AF55FEAA8A239C89: 0x1,  # noqa: E501
            0x689082D076EC3C02CBE4B99F6D9833E3C4A161072FD42FB7649EEE5189A67CCC: 0x63524E3FE4791AEFCE1E932BBFB3FDF375BFAD89,  # noqa: E501
            0xAF1D6676BE3AB502A59D91F6F5C49BAFFC15B2CFC65A41C4D96857C0F535ADBA: 0x1D60000000000000000,  # noqa: E501
            0xDF1A770F69D93D1719292F384FDB4DA22C0E88AEF2BA462BFF16674BC7848730: 0x1C11AA45C792E202E9FFDC2F12F99D0D209BEF70,  # noqa: E501
            0xEC5E7F54FA5E516E616B04F9D5A0EE433A80E09ED47D7E5269AFD76C05FF251E: 0x2,  # noqa: E501
        },
        nonce=0,
        address=Address("0xe509e3a93beb1eba72f8cb8d25f93a85e2d54afb"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x67F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0xAC],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x2F300BEE)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x44))
            + Op.ADD(Op.MLOAD(offset=0x80), 0x2)
            + Op.DUP1
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.DUP2, value=0x10000000000000000)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, Op.MUL(0x20, Op.MLOAD(offset=0x80))),
                value=Op.MLOAD(offset=0x60),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.DUP3,
                    Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x80), 0x1)),
                ),
                value=Op.SUB(Op.MLOAD(offset=0x40), 0x1),
            )
            + Op.DUP1
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2C8, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xA647A5B9))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(
                offset=0x100,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x4)
                ),
            )
            + Op.MSTORE(
                offset=0x160,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x24)
                ),
            )
            + Op.MSTORE(
                offset=0x180,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.MSTORE(offset=0x1A0, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x84))
            + Op.POP
            + Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x100), 0x20))
            + Op.DUP1
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1D5,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x1A0))),
            )
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x162,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.ADD(
                Op.DUP3,
                Op.MUL(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x160),
                            Op.MUL(
                                0x20,
                                Op.ADD(
                                    Op.MUL(Op.DUP6, Op.MLOAD(offset=0x80)),
                                    Op.DUP2,
                                ),
                            ),
                        ),
                    ),
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x100),
                            Op.MUL(0x20, Op.DUP1),
                        ),
                    ),
                ),
            )
            + Op.SWAP2
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x12E)
            + Op.JUMPDEST
            + Op.POP
            + Op.SDIV(Op.DUP2, 0x10000000000000000)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C8,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP6, Op.MUL(0x20, Op.DUP2)),
                value=Op.SUB(
                    Op.MLOAD(offset=Op.ADD(Op.DUP6, Op.MUL(0x20, Op.DUP2))),
                    Op.SDIV(
                        Op.MUL(
                            Op.MUL(
                                Op.DUP5,
                                Op.MLOAD(
                                    offset=Op.ADD(
                                        Op.MLOAD(offset=0x160),
                                        Op.MUL(
                                            0x20,
                                            Op.ADD(
                                                Op.MUL(
                                                    Op.DUP7,
                                                    Op.MLOAD(offset=0x80),
                                                ),
                                                Op.DUP3,
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.MLOAD(offset=0x180),
                                    Op.MUL(0x20, Op.DUP4),
                                ),
                            ),
                        ),
                        0x100000000000000000000000000000000,
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x174)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x11E)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x203,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.ADD(
                Op.DUP3,
                Op.MUL(
                    Op.MLOAD(offset=Op.ADD(Op.DUP5, Op.MUL(0x20, Op.DUP2))),
                    Op.MLOAD(offset=Op.ADD(Op.DUP4, Op.MUL(0x20, Op.DUP1))),
                ),
            )
            + Op.SWAP2
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1DB)
            + Op.JUMPDEST
            + Op.POP
            + Op.SDIV(Op.DUP2, 0x10000000000000000)
            + Op.SWAP1
            + Op.POP
            + Op.SDIV(Op.DUP2, 0x2)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x242, condition=Op.ISZERO(Op.SLT(Op.DUP2, 0xB)))
            + Op.SDIV(
                Op.ADD(
                    Op.DUP4,
                    Op.SDIV(Op.MUL(Op.DUP6, 0x10000000000000000), Op.DUP3),
                ),
                0x2,
            )
            + Op.SWAP2
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x219)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x276,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP6, Op.MUL(0x20, Op.DUP2)),
                value=Op.SDIV(
                    Op.MUL(
                        Op.MLOAD(
                            offset=Op.ADD(Op.DUP7, Op.MUL(0x20, Op.DUP3))
                        ),
                        0x10000000000000000,
                    ),
                    Op.DUP2,
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x246)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, Op.MUL(0x20, Op.MLOAD(offset=0x80))),
                value=Op.SUB(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x100),
                            Op.MUL(0x20, Op.MLOAD(offset=0x80)),
                        ),
                    ),
                    0x1,
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.DUP3,
                    Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x80), 0x1)),
                ),
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x100),
                        Op.MUL(0x20, Op.ADD(Op.MLOAD(offset=0x80), 0x1)),
                    ),
                ),
            )
            + Op.DUP1
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x379, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x5B180229))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(
                offset=0x300,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x4)
                ),
            )
            + Op.MSTORE(
                offset=0x320,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x24)
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x44))
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x33F,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.ADD(
                Op.DUP3,
                Op.SDIV(
                    Op.MUL(
                        Op.MLOAD(
                            offset=Op.ADD(
                                Op.MLOAD(offset=0x300),
                                Op.MUL(0x20, Op.DUP3),
                            ),
                        ),
                        Op.MLOAD(
                            offset=Op.ADD(
                                Op.MLOAD(offset=0x320),
                                Op.MUL(0x20, Op.DUP2),
                            ),
                        ),
                    ),
                    0x10000000000000000,
                ),
            )
            + Op.SWAP2
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x306)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x366,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.EQ(Op.MLOAD(offset=Op.MLOAD(offset=0x320)), 0x0)
                    ),
                ),
            )
            + Op.SDIV(
                Op.MUL(Op.DUP4, 0x10000000000000000),
                Op.MLOAD(offset=Op.MLOAD(offset=0x320)),
            )
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=0x36B)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.POP
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x380, value=Op.DUP2)
            + Op.RETURN(offset=0x380, size=0x20)
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x571, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xF4CA7DC4))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(
                offset=0x3A0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x4)
                ),
            )
            + Op.MSTORE(
                offset=0x3C0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x24)
                ),
            )
            + Op.MSTORE(offset=0x1A0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x64))
            + Op.POP
            + Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x3C0), 0x20))
            + Op.EXP(Op.MLOAD(offset=0x80), 0x2)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x44D,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x441,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.DUP5,
                    Op.MUL(
                        0x20,
                        Op.ADD(
                            Op.MUL(Op.DUP5, Op.MLOAD(offset=0x80)), Op.DUP2
                        ),
                    ),
                ),
                value=Op.ADD(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.DUP5,
                            Op.MUL(
                                0x20,
                                Op.ADD(
                                    Op.MUL(Op.DUP5, Op.MLOAD(offset=0x80)),
                                    Op.DUP2,
                                ),
                            ),
                        ),
                    ),
                    Op.SDIV(
                        Op.MUL(
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.MLOAD(offset=0x3A0),
                                    Op.MUL(0x20, Op.DUP4),
                                ),
                            ),
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.MLOAD(offset=0x3A0),
                                    Op.MUL(0x20, Op.DUP2),
                                ),
                            ),
                        ),
                        0x10000000000000000,
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x3F1)
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x3E4)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.DUP2
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.MUL(Op.MLOAD(offset=0x1A0), Op.MLOAD(offset=0x80))
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x51E,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x1A0))),
            )
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x512,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x506,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.DUP6,
                    Op.MUL(
                        0x20,
                        Op.ADD(
                            Op.MUL(Op.DUP6, Op.MLOAD(offset=0x80)), Op.DUP3
                        ),
                    ),
                ),
                value=Op.ADD(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.DUP6,
                            Op.MUL(
                                0x20,
                                Op.ADD(
                                    Op.MUL(Op.DUP6, Op.MLOAD(offset=0x80)),
                                    Op.DUP3,
                                ),
                            ),
                        ),
                    ),
                    Op.SDIV(
                        Op.MUL(
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.MLOAD(offset=0x3C0),
                                    Op.MUL(
                                        0x20,
                                        Op.ADD(
                                            Op.MUL(
                                                Op.DUP7, Op.MLOAD(offset=0x80)
                                            ),
                                            Op.DUP3,
                                        ),
                                    ),
                                ),
                            ),
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.DUP8,
                                    Op.MUL(
                                        0x20,
                                        Op.ADD(
                                            Op.MUL(
                                                Op.DUP4, Op.MLOAD(offset=0x80)
                                            ),
                                            Op.DUP3,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        0x10000000000000000,
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x4AD)
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x4A0)
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x492)
            + Op.JUMPDEST
            + Op.DUP2
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x552, condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.DUP5)))
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP5, Op.MUL(0x20, Op.DUP2)),
                value=Op.SUB(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x3C0),
                            Op.MUL(0x20, Op.DUP2),
                        ),
                    ),
                    Op.MLOAD(offset=Op.ADD(Op.DUP3, Op.MUL(0x20, Op.DUP1))),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x526)
            + Op.JUMPDEST
            + Op.POP
            + Op.DUP2
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x69D, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x232B2734))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(
                offset=0x620,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x4)
                ),
            )
            + Op.MSTORE(
                offset=0x280,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x24)
                ),
            )
            + Op.MSTORE(
                offset=0x3C0,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x44)
                ),
            )
            + Op.MSTORE(offset=0x640, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x1A0, value=Op.CALLDATALOAD(offset=0x84))
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0xA4))
            + Op.POP
            + Op.JUMPI(
                pc=0x602,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=Op.MLOAD(offset=0x280)), 0x0),
                ),
            )
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x600,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x280), Op.MUL(0x20, Op.DUP2)),
                value=Op.SUB(
                    0x0,
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x280),
                            Op.MUL(0x20, Op.DUP1),
                        ),
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x5D4)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x67F,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x1A0))),
            )
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x673,
                condition=Op.ISZERO(Op.SLT(Op.DUP2, Op.MLOAD(offset=0x80))),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x620), Op.MUL(0x20, Op.DUP3)),
                value=Op.ADD(
                    Op.MLOAD(
                        offset=Op.ADD(
                            Op.MLOAD(offset=0x620),
                            Op.MUL(0x20, Op.DUP3),
                        ),
                    ),
                    Op.SDIV(
                        Op.MUL(
                            Op.MLOAD(
                                offset=Op.ADD(
                                    Op.MLOAD(offset=0x3C0),
                                    Op.MUL(
                                        0x20,
                                        Op.ADD(
                                            Op.MUL(
                                                Op.DUP6, Op.MLOAD(offset=0x80)
                                            ),
                                            Op.DUP3,
                                        ),
                                    ),
                                ),
                            ),
                            Op.SDIV(
                                Op.MUL(
                                    Op.MLOAD(offset=0x640),
                                    Op.MLOAD(
                                        offset=Op.ADD(
                                            Op.MLOAD(offset=0x280),
                                            Op.MUL(0x20, Op.DUP3),
                                        ),
                                    ),
                                ),
                                0x10000000000000000,
                            ),
                        ),
                        0x10000000000000000,
                    ),
                ),
            )
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x613)
            + Op.JUMPDEST
            + Op.POP
            + Op.ADD(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x605)
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x620)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0xf1562e1c0d0baa3ea746442bb7f11153fcf5cfda"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "36a560bd00000000000000000000000000000000000000000000000000000000000f69b5"  # noqa: E501
        ),
        gas_limit=3000000,
        gas_price=10000000000000,
    )

    post = {
        callee_5: Account(
            storage={
                0x65D5EFDFCC0FBA693DC9E467F633097FFDC97401901463AD0E28855486D1EDF: 0xB9D69098A6ACFE0C6411BCAAF430F78D363A9ADC32B78BC2E15CCD6E883E9784,  # noqa: E501
                0x12643FF300762717D27EFB567B82C65560D7B43249D908504E5510863AB82AAC: 0x154CF60E137C594516A065149610B6A3989396A42581D5FD8919E711C55DA225,  # noqa: E501
                0x1489023D18C5D10427C4AA8DC726E840EB5AE7F604A8E9243C61634FB009E4D7: 5,  # noqa: E501
                0x1489023D18C5D10427C4AA8DC726E840EB5AE7F604A8E9243C61634FB009E4D8: 1,  # noqa: E501
                0x19EFB13D6576359514ACE5211988A8D51379FA88CCD2B886B409F842B13D7932: 0xC849CC595B452D11C206D2EB8CDFA06DE211E3FF19EE0E0276DC857C05D4FE,  # noqa: E501
                0x1B37E91BF8580C7C6BCF8CDFF25C7ED78180124A94AF6F30C40D476A3D079AD6: 0xABA4CD295118A482A0A62579E35E4BA5BDD76146CC9E4D96172FCE8BE8977AB4,  # noqa: E501
                0x2BF9FD8FACDD6FD9C84657F5AD7381A5AECF670CDA68CB3C5829B6532C865506: 0x53098A1D111586DBCC0D051846284F5803C63C313E7F7E6D84430435D11D4C50,  # noqa: E501
                0x3111BFD25728C0ADFAD0F8C1AD79CB1B91167267DECA98DE88F156ED25CAEEDC: 0xAD393086F30B49511B08FDD27AC78810B084C7CD7DE6AC354F614C18EA9E7DF4,  # noqa: E501
                0x3379E7AE125C5C5D623D1D993C1459B61D6723B1C30D1AA026C48F6A6155B8EA: 0x8C4183732567A99A8A718E363391E102532F9A640E42968CF2354D9ACC908BB0,  # noqa: E501
                0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE2: 1,  # noqa: E501
                0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE3: 1,  # noqa: E501
                0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE4: 1,  # noqa: E501
                0x34CABE0C7E64A2CAA93FD8D6A0DEFC07ACB9D44B13430FA3AE9282FFFD40DEE5: 1,  # noqa: E501
                0x39050607FE892059A6344AB0F594F382FB0B345CAB373497246DBE86FE7E14E7: 0x2B3BCA833E482737E7E47B1568E6F890F8E1666490D38FE130ABD6F0CCB109CF,  # noqa: E501
                0x417BE8BC6791807372E0222A350BB8A5D67BBC8D7595C301D8A5A8372CFDCEF1: 0xABD4971B4605A7155802F70E08298B1CEB0E4E4EACCCCD348F77A77227F73A7F,  # noqa: E501
                0x41E9A54B3EE0C276AA076BABB161DE12B0F8916B47F8F6FB85CC387CF34696DD: 0x22F2F444EBDA9D2913FFEF5059B039EC9B5876AA71821991C2515BF79F64935E,  # noqa: E501
                0x45CEB8DA6FB8936592D3BCE4883F1A6A34D636F559E0A1070A5802A65AC39BD5: 0x57A5122FF3BF737B0DE0F9F08011A8648C19E43FF071FB7086234723C9383F1F,  # noqa: E501
                0x4AA6B934608A45C8F53A945C05DDEE1814A3B9F63A048FC7AD3D47E67156F024: 0xD03862BECEDADA67B4825A0238F3E67495CCB595CD7D08F1BD5D3160644B9299,  # noqa: E501
                0x4B8B58F0B0E326A5907D1A810E5FF31E05B4CAB45125B776DB8577E7DBC46BCE: 0x2F0000000000000000,  # noqa: E501
                0x4C33460347337BFC7DF08BF182988301B7B426A27A67F1C6C634F637C60E87AC: 0xBAB4AB2AD4EAFE7C84EF6A8CD69157D9CE6B843793A2CD0877B8E91F63CB2D4D,  # noqa: E501
                0x58DA0C0C256BBA101CE36FAD8BF838717A57E6AB850A191DC9C09DA9CE56BF1B: 5,  # noqa: E501
                0x5CB38B16DB1D632086D4AF695DE7F5F242A6E40947067F96EDD566FE2AC438EF: 0x6D0BE832B2007EA28CDA705B73922CBF9794C5A25B89BD2F28B7347ED2B96C86,  # noqa: E501
                0x64A9621CC4BA92BF738C55010C609DFAA3972A1138C30B5ADCEF1BA2363B360E: 0xD7953BFE8CB591F129FD0862A9E9C421151E2B5831560FF5215D23F751364B35,  # noqa: E501
                0x696664A5F0AB5ACD9304A377FB684F2D3FE6BB60B8A95CB2BDBB57DB767E7A84: 0x154CF60E137C594516A065149610B6A3989396A42581D5FD8919E711C55DA225,  # noqa: E501
                0x69AD1D19E617936ABDF05133BF268DC8CED6B518F22B249B5860967D07006487: 0x8C803B48B383DDABD1B3AFE858EFB48C203229B7317DD76149DDDAB4253B858A,  # noqa: E501
                0x70B3BF53996FAC325EB67608A4EEB0CD0B55DEF6255D7ED42AD28EC07238B5D6: 0x45E9723E9232B37207ECAC1C97B8647D053625A578D450F7456280B2FF8EFC27,  # noqa: E501
                0x7A9DCEE62E3E02CC8E020F372DF2EFDEB835F091C1EF1DBE221072D1095AABD2: 0x2F0000000000000000,  # noqa: E501
                0x7E4D8C0F6D8ABB4CE1AE45B254046ACEEDABFA9548851B8B5D3E2C0637C985FD: 11,  # noqa: E501
                0x7E95F3CC3315D289C52253BAABA29B1B00C86816E6B788D50795279A8BAA00DB: 0x45E9723E9232B37207ECAC1C97B8647D053625A578D450F7456280B2FF8EFC27,  # noqa: E501
                0x8DA187157087529EE4E9C381F8E3149C56ACF3BDFDA29B8B9B4532F24B83F5FE: 0x8C4183732567A99A8A718E363391E102532F9A640E42968CF2354D9ACC908BB0,  # noqa: E501
                0x9001F91DDAEF87BC067886E874C0749998C9B58B2EC8472CA014CA8B55F88578: 0xFB76974EEFCA01F33FB38646C2D3C1536F1A763D7AFF53AB7F877D4C5EA7FD0,  # noqa: E501
                0x9ED0CEDD2A9A78D949F40019F53D10031AEF6ED342C97E01FC03B481EE56B3CB: 4,  # noqa: E501
                0x9FDDF1DB29CAA5C1239EDD86E9E0835CDFE41F7253EC78F62D3DA8558D6F3CD7: 0x104EEF8FA35BF39F677D81855BC0B9F42317F32792E98E95E4DF441DEB634211,  # noqa: E501
                0xA0953566119395C11186B334805FC1A16175ECAC0ECC93AE0322264F0DC2E40D: 0x10C5A00466AB7C0ADAE1E93537CC275EA8CF23FF509D5466A1FD6F56B0A61D1B,  # noqa: E501
                0xAA0DBF8241EF3AE07C254E6869E84895BA2BE0779A7F261C8308A3114BE1C54A: 4,  # noqa: E501
                0xAFFE808B495D13A14391CE5F27C211C36DA12826969CD7841EE0D81E5B900E2D: 1,  # noqa: E501
                0xAFFE808B495D13A14391CE5F27C211C36DA12826969CD7841EE0D81E5B900E2E: 1,  # noqa: E501
                0xB4A2B68C48EF78AEB641EE538FAD51781022FD23ED9D93D211017DB6A02376CE: 0xFBC06642245CF2FED7ED46EA0A18A7185830B6F2C4E0A4CA55246041E8BFA72,  # noqa: E501
                0xBA8D79990898383919E437F2458B93B340072C89D963808D9E04F51858E3C5EC: 0x41D2CAC534D90A0DBD199117481A63E32CC11411DAB2EAA36C91C0EEC62823CF,  # noqa: E501
                0xBB3BC1A2015123750DF57D4CEFF7E28CB847910B79B34841DE905B59A8BB177C: 0x734417EB19E1873427257F1EA1594748C16CFA866A7B7CF896E281F2EC774A40,  # noqa: E501
                0xBF30CDCB83AB2BD5F5EEE691FFA4107B58B75BA6A5C2E6754D4C5C0437F2876C: 5,  # noqa: E501
                0xC2A26B80067FC36B8268B0D5B31AFFF953FA91CEBEA39F191E2763D6E71259B9: 0x2A43C547FE8DE2400D2A141016550E8BAE058D41164247C099E787DDD40E789,  # noqa: E501
                0xC98339D275EEF16E0562CA8521212CEF61AA0F39B12E2A27502AAA97A9E5E70F: 0x5A3DE2A5C268CDB75F4B01507AA80C4E4A1BC67BCB0DF265BBB00060774E5978,  # noqa: E501
                0xCBD6AE6BD61BC9270EC836F1919B3268113ABE076C7FEBFDB8CF573B199CE9A9: 0xF402B17773C1F7534034EE58DC0D2A3421470A7A67DAF4FA790DC3B420EEF790,  # noqa: E501
                0xD2C8CBB562FCCD0C9A3D0D491B7F65CC6A89856498F933427D9D21B745B9D50E: 0x3625A26FDB7B747501F1EE2500F98C49D9CD290383A21254587C3C49D2805321,  # noqa: E501
                0xD66F52A4E24585238CCC03443B2FDB8B2B100259BC7260F39097C7C339211FFE: 0x1641851904381915C86B60DF7E288896FB5F8EBAD65D594829FB9F2B59CD1DA6,  # noqa: E501
                0xD8F720C05A5526DD621D1831AE122ABDDD3DFECD8B63B0BA4C92FA7B2ADE44FF: 0xAD393086F30B49511B08FDD27AC78810B084C7CD7DE6AC354F614C18EA9E7DF4,  # noqa: E501
                0xDC22D3171B82817C910BBEAC1F8B50C8DE99F8C524F172AEF3491981BD5ED4FB: 0x94B8CBA4EA090D1C392FBC94B82FB9EF9F468A15BBC537F4D051776F4D422B1D,  # noqa: E501
                0xDCE8ADBDEFA929DBE60245F359446DB4174C62824B42E5D4D9E7B834B4D61DEB: 0x2C9069845B2E74C577FF1CD18DF6BC452805F527A9EE91FD4A059E0408B5DEA6,  # noqa: E501
                0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D196: 1,  # noqa: E501
                0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D197: 1,  # noqa: E501
                0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D198: 1,  # noqa: E501
                0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D199: 1,  # noqa: E501
                0xDD9493073DB9E42FD955E834C89A74089F99196186EE0B2688124989BE00D19A: 1,  # noqa: E501
                0xE54F074C81BFA60B5BF413934C108086298B77291560EDFEEAD8AA1232E95236: 0xF40AAA24323C9E6983CCFFAFEEBE4B426509B901E8C98B8A40D881804804E6B,  # noqa: E501
                0xE66C0F55F66C752EDF73027D45B7B1AE729AE15E1C67C362DBC6F25EDF8D76FF: 1,  # noqa: E501
                0xE983D899F807BBCB5881F2DDF875B2EBB5CB8A7A4E77A8C98A40AAAE6A468735: 0x6D0BE832B2007EA28CDA705B73922CBF9794C5A25B89BD2F28B7347ED2B96C86,  # noqa: E501
                0xED7D6E2D40FBD5046412FFAD1C45B63D87C6197182D6DBC66BB1E5C6E4DED5C7: 0xABA4CD295118A482A0A62579E35E4BA5BDD76146CC9E4D96172FCE8BE8977AB4,  # noqa: E501
                0xF043B5A1952847579F233706A8F130889A484D2DA3E574FDD5859F05AAF52111: 2,  # noqa: E501
                0xF40F4CFDACB62DD799F36B580349FAC1F4A4CAF8DD3383CC387C35ADB6574E21: 0x2F0000000000000000,  # noqa: E501
                0xF60FA6E25E9028A6DC6B26BBC1EADAE3DA157DF0D1D6F6628BC33CAD68A7E455: 0x2D7D00618C059EBE40593B9497C633E1AC6E161DADBD5BB734C2663CD3E8A8E1,  # noqa: E501
                0xFD280AC5182D5B2366122F38ACFA6DC471240FFDE9D5FEB985CE7A2325C960E7: 3,  # noqa: E501
            },
        ),
        callee_8: Account(
            storage={
                0: 1,
                0xA4470E9D0419DF71F6257FCDFD2C0A3BAD96A23F5AB414BC10AAF1A31A536A7: 0xB4876148229C22BD2291F1A4F5468C8C789B23639370C4D447F270BA341DBBEC,  # noqa: E501
                0x16EF4193A274568D283FF919C299729E07696D9ADA48187B81D68E12E7B962DE: 0xA103C04E7ECB9B3395F77C7B0CAD28E62C85F042DE4767CCC6C005E6F47F8D4,  # noqa: E501
                0x1F1866E966F321B84535705846689749D34D5DC02994613E2931973C605D9E93: 0xC723D0AA4A60529FE42277C8094AA19263AFF36650136EFC5EDFD0785D457634,  # noqa: E501
                0x252A4EC7133643FDDCDB22A86C415F78B2DD251F18D1EFCD6A44ACF590C4AE72: 0x9CAF94B82715869E71D3CEE986094EA612F0258570B7E5EF47B5D09E9515322B,  # noqa: E501
                0x41B451E8D86D28ADD758CBD3F48A18FD04B11A80288C1DC434A5BF2D8FB1CA64: 0xB602498F12A8B4AF3A1FCA357CEA6B19BCD163DFEC1D845364CE1395F7C21FA7,  # noqa: E501
                0x491D10658C1EC762152D8AD2D890AD59111B1EE7B4BC25736046923D3534D9A5: 25246,  # noqa: E501
                0x5B0E8552EFD72A845E47318ABBBEF9DC9FCDFE0D1A06CDA44494401301581511: 0xFBC98F4017AE5C20459DAADAA6BEE519B6DE871D3DBAA9AB3F34340FEF4CB643,  # noqa: E501
                0x5B672A107BA6FAB01CBDDF079042E9F6176A8E6F154584FC4DF4B15674C9456E: 0x1603DA41D610854D85536B37D000E5EB7CA09786C43F50E7441C0AFBFF1DE0A9,  # noqa: E501
                0x605B934BD26C9ECDF7029A7DC062D3A6B87338511CFF96E0C5F13DE9EEA3462E: 0xF0D24F3D0EDA573FC5D43E3D0680993C51293752CD6DE205040D3197F412F475,  # noqa: E501
                0x618355E25491DFE86175F9D9B3147E4D680AA561D98384E3621DC6A3088B0846: 0x6B2E6D2D5DEB27DFFEC973F23AF4CAF111E66D1397F467DBBEDF5AB2192FB6B6,  # noqa: E501
                0x65112936BEC0F1E84FDA6623FB54E12BAADC8A4A208C8C4EB3ED5E79CBD7E85F: 0xA59AC24E3E0663413D0F87516BA8FB44C6C3E14DA8EAABBDE80F8EE285F65934,  # noqa: E501
                0x687CB2122DE7BACF42B9CD380B04FF2A2CE92A0B63706A9A78263B3CE86F3313: 0x200000000000000,  # noqa: E501
                0x72A539B064C98D29A514EE55694225E05FB41FE63E5FE710E4536BD9BA3591B4: 0x338ECFE6C523ED1184918B19584D97DD1095ECAADC49C7BA9DA62B8B513026E0,  # noqa: E501
                0x7AEB0A0CE8882A12D853078382A2BC72F7A94AF6109F167DE37B36C0A7DEB828: 0x4C428400EA8A7BD7C46BA9895B508770EFA4551F0D793E1BEB1207DA01D9962F,  # noqa: E501
                0x7C8F4A98E086F64E28C75F54712B5D44BEC3C29B5C70519E8880D3046A5618DC: 0xAAFC1F2601752B114D722070F75539BFEC7FAF49F0D48A48D27862F0C3B09903,  # noqa: E501
                0x809C325F50ACF5787776E960985E72443B4330AD1E2F466557FFFEE16BA51D44: 0xB940A56E64B5B661D87919B8EF03640EC077A6D72DD0B524ADEDAA7DDC91FF7A,  # noqa: E501
                0x84E4A80D33C5D2ABD2B0A5AEC0FDC5EAEED90AB31DB556E404A81718EA286E39: 28,  # noqa: E501
                0x877305412FA2486F563C457B744E5C8B1E4D0ECA73371DE5E771F2ABC263F4DC: 0x7088A36F67276D475AA62127CFDE9790CC802FDF3A54DF49461A25EB8BF15707,  # noqa: E501
                0x922A8F2FC1CBE67C8ACC6A8A720983C366D71D3E2E78E3048949EBC913EA611A: 0x50FB9F913CA102534BB0A8EB8EBF19C68DFD16FFE5E207BCC580084CD4ECD8B4,  # noqa: E501
                0x987CB9ECFD8CE499D9D0E9E6B7DA29617AA02774A34F4A8EA54442F44A1E1936: 0x5179F98F555F1E9F1D4A335D16F41154579A53E361E9859269B6FA74EA9C7D21,  # noqa: E501
                0xADA5013122D395BA3C54772283FB069B10426056EF8CA54750CB9BB552A59E7D: 0xF69B5,  # noqa: E501
                0xB16B117660F31197087F4D6FE50D3D4579152244956F753F9653CCF85F4B35C4: 0x830272E3BB35226B047244CBDC46F1B6B864A280461E7A592F70E0863F4F1D33,  # noqa: E501
                0xB1F1AAEDFB83C7755A2BFFC9E2557F1723F9ABE5642397963E76248C9209AF57: 0xE9BE955C5FBFCD846D7425EAEA05CE897786AEFAD99665342CBF30761B352526,  # noqa: E501
                0xB7BD50FDF7B043411C9AC33F0AF2CEBC69C393EB0B91F4976946F9C7B15AD0DA: 0xFCCCA0E7832BAE9AFE799A6D6177DC3869FA6C5B5105F8DF6F365DE5723820EC,  # noqa: E501
                0xBC96058EB03504EE6F5C0A9582F8720D99A6E9738B171499507FACFF0B2C0B5B: 0x9DB6A4F2766B51013B8D2F9038131D1BB4AF725D019D111D7E26FF96C023B23F,  # noqa: E501
                0xC186C4F377B7F13892ADE9656ACD1522AA1F8AC151AC4F62457B5073241D79FC: 0x7289738FEF00F1770EEB098DB9BD486C01AC12398D79CDF935514A128C585C51,  # noqa: E501
                0xCAE57AE3017972D63EFFD8EAE44F5054402C3E890D154B905ED6B5B533327FA9: 0xD2E4BF465E61993D13089B940A7C55017A5117D8E43E4115550A139E1D4B3E3A,  # noqa: E501
                0xCF569EE7BF3ACCC0F893DFFD04F1A757F373EFE80893EFF504FB3678F688EC1D: 3,  # noqa: E501
                0xD69B7284545A9F5275DF64CE94848DC954FCB8A8B525E7AC801517C12A75AF84: 0x4202995350ABAE303B43E564AA79121A30B5F1AEA31F69CD25E07DD3FA64DCE7,  # noqa: E501
                0xD8F6F90F51E657690EE28D1CC80D81BC1B89290065891FDD853D09CAAAF756AA: 1,  # noqa: E501
                0xDE72F8EED43CC2A5A3EAA51483D14B17DC92BB26C154AE184CEE4B4895011EDC: 0x47CE2B6FDB72C3FABB9C74F82C1E3E522BCD42E614FD85C208AC3C4C840CEA72,  # noqa: E501
                0xE0E687DDF317F3D2B209AE3884148EFF0F636E16827F82EDED14ADA8FC603009: 0xFA7C8939F9B033162CF8D75EA69671BB8A27041BD4CDC76594E61E99333CB041,  # noqa: E501
                0xE8CDA339D72A1A350B62F1E3FA52E254C395CC9FDD9F60ADB21C7633FBDAB531: 0x128C4FDF4801A30EAE99DD58F0F3FF5CA65F71B66A9AC0F38DD450FB24B4AAAA,  # noqa: E501
                0xEC5E7F54FA5E516E616B04F9D5A0EE433A80E09ED47D7E5269AFD76C05FF251E: 20,  # noqa: E501
                0xF9A3BF5F2CCB903EE1A7644113B794DB0260DE404FB8F11203E75A7FFF151618: 0xBD94773C0D85C68240AE8DFD53D9D33CD137509BFC5D3433381299DF768C8377,  # noqa: E501
            },
        ),
        callee_9: Account(
            storage={
                0xF299DBBE3A7A5D949FE794E9A47B3106699C8110FF986EB84921C183E69E7F0: 0x2F0000000000000000,  # noqa: E501
                0x1EDCD36F61CAE5DC6414157DFBADF9F11CA013AC763E27F8AF55FEAA8A239C89: 1,  # noqa: E501
                0x689082D076EC3C02CBE4B99F6D9833E3C4A161072FD42FB7649EEE5189A67CCC: 0x63524E3FE4791AEFCE1E932BBFB3FDF375BFAD89,  # noqa: E501
                0xAF1D6676BE3AB502A59D91F6F5C49BAFFC15B2CFC65A41C4D96857C0F535ADBA: 0x1D60000000000000000,  # noqa: E501
                0xDF1A770F69D93D1719292F384FDB4DA22C0E88AEF2BA462BFF16674BC7848730: 0x1C11AA45C792E202E9FFDC2F12F99D0D209BEF70,  # noqa: E501
                0xEC5E7F54FA5E516E616B04F9D5A0EE433A80E09ED47D7E5269AFD76C05FF251E: 2,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
