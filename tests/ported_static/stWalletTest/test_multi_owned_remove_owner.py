"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json
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
    ["tests/static/state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_multi_owned_remove_owner(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(pc=Op.PUSH2[0x65], condition=Op.EQ(Op.DUP2, 0x173825D9))
            + Op.JUMPI(pc=Op.PUSH2[0xB7], condition=Op.EQ(0x2F54BF6E, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0xE8], condition=Op.EQ(0x7065CB48, Op.DUP1))
            + Op.JUMPI(pc=0x105, condition=Op.EQ(0xB75C7DC6, Op.DUP1))
            + Op.JUMPI(pc=0x142, condition=Op.EQ(0xBA51A6DF, Op.DUP1))
            + Op.JUMPI(pc=0x15F, condition=Op.EQ(0xF00D4B5D, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x181]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x0]
            + Op.CALLDATASIZE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1
            )
            + Op.SWAP1
            + Op.SWAP2
            + Op.SHA3
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x46D]
            + Op.DUP2
            + Op.JUMPDEST
            + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
            + Op.DUP2
            + Op.DUP1
            + Op.DUP1
            + Op.JUMPI(pc=0x58F, condition=Op.ISZERO(Op.EQ(Op.DUP2, Op.DUP4)))
            + Op.JUMP(pc=0x586)
            + Op.JUMPDEST
            + Op.PUSH2[0x187]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMPDEST
            + Op.PUSH20[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.AND
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
            + Op.GT
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH2[0x181]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x0]
            + Op.CALLDATASIZE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1
            )
            + Op.SWAP1
            + Op.SWAP2
            + Op.SHA3
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x37C]
            + Op.DUP2
            + Op.JUMP(pc=Op.PUSH2[0x80])
            + Op.JUMPDEST
            + Op.PUSH2[0x181]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
            + Op.SWAP1
            + Op.DUP1
            + Op.DUP1
            + Op.JUMPI(pc=0x191, condition=Op.ISZERO(Op.EQ(Op.DUP2, Op.DUP4)))
            + Op.JUMP(pc=0x213)
            + Op.JUMPDEST
            + Op.PUSH2[0x181]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x0]
            + Op.CALLDATASIZE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1
            )
            + Op.SWAP1
            + Op.SWAP2
            + Op.SHA3
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x533]
            + Op.DUP2
            + Op.JUMP(pc=Op.PUSH2[0x80])
            + Op.JUMPDEST
            + Op.PUSH2[0x181]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x40]
            + Op.PUSH1[0x0]
            + Op.CALLDATASIZE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1
            )
            + Op.SWAP1
            + Op.SWAP2
            + Op.SHA3
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x286]
            + Op.DUP2
            + Op.JUMP(pc=Op.PUSH2[0x80])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
            + Op.MSTORE(offset=0x20, value=0x103)
            + Op.SHA3(offset=Op.DUP2, size=0x40)
            + Op.SLOAD(key=Op.ADD(Op.DUP2, 0x1))
            + Op.PUSH1[0x2]
            + Op.DUP5
            + Op.SWAP1
            + Op.EXP
            + Op.SWAP3
            + Op.SWAP1
            + Op.DUP4
            + Op.AND
            + Op.DUP2
            + Op.SWAP1
            + Op.JUMPI(pc=0x213, condition=Op.ISZERO(Op.GT))
            + Op.SLOAD(key=Op.DUP2)
            + Op.PUSH1[0x1]
            + Op.ADD(Op.DUP5, Op.DUP1)
            + Op.SLOAD(key=Op.DUP1)
            + Op.SWAP2
            + Op.SWAP1
            + Op.SWAP3
            + Op.SSTORE(key=Op.DUP5, value=Op.ADD)
            + Op.DUP5
            + Op.SWAP1
            + Op.SUB
            + Op.SWAP1
            + Op.SSTORE
            + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x40]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.PUSH1[0x60]
            + Op.DUP7
            + Op.SWAP1
            + Op.MSTORE
            + Op.PUSH32[
                0xC7FB647E59B18047309AA15AAD418E5D7CA96D173AD704F1031A2C3D7591734B  # noqa: E501
            ]
            + Op.SWAP1
            + Op.DUP1
            + Op.LOG1
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.ADD
            + Op.SSTORE
            + Op.PUSH20[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.AND(Op.DUP2, Op.DUP5)
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.PUSH1[0x40]
            + Op.SHA3(offset=Op.DUP3, size=Op.DUP1)
            + Op.DUP3
            + Op.SWAP1
            + Op.SSTORE
            + Op.SWAP3
            + Op.DUP7
            + Op.AND
            + Op.MSTORE(offset=Op.DUP3, value=Op.DUP1)
            + Op.SWAP1
            + Op.DUP4
            + Op.SWAP1
            + Op.SHA3
            + Op.DUP6
            + Op.SWAP1
            + Op.SSTORE
            + Op.SWAP1
            + Op.DUP3
            + Op.MSTORE
            + Op.PUSH1[0x60]
            + Op.MSTORE
            + Op.PUSH32[
                0xB532073B38C83145E3E5135377A08BF9AAB55BC0FD7C1179CD4FB995D2A5159C  # noqa: E501
            ]
            + Op.SWAP1
            + Op.DUP1
            + Op.LOG1
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x27F, condition=Op.ISZERO)
            + Op.PUSH2[0x294]
            + Op.DUP4
            + Op.JUMP(pc=Op.PUSH2[0xBE])
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x29F, condition=Op.ISZERO)
            + Op.POP
            + Op.JUMP(pc=0x281)
            + Op.JUMPDEST
            + Op.AND(Op.DUP5, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
            + Op.SWAP3
            + Op.POP
            + Op.DUP3
            + Op.JUMPI(pc=0x2D5, condition=Op.ISZERO(Op.EQ))
            + Op.POP
            + Op.JUMP(pc=0x281)
            + Op.JUMPDEST
            + Op.PUSH2[0x2F7]
            + Op.JUMPDEST
            + Op.SLOAD(key=0x104)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x80C, condition=Op.ISZERO(Op.LT(Op.DUP2, Op.DUP2)))
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.DUP3
            + Op.SWAP1
            + Op.DUP2
            + Op.JUMPI(pc=0x854, condition=Op.LT)
            + Op.STOP
            + Op.JUMPDEST
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x2]
            + Op.DUP4
            + Op.JUMPI(pc=0x21A, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ADD
            + Op.SSTORE
            + Op.SLOAD(key=0x1)
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.PUSH2[0x102]
            + Op.PUSH1[0x20]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.PUSH1[0x40]
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP1
            + Op.SHA3
            + Op.SWAP4
            + Op.SWAP1
            + Op.SWAP4
            + Op.SSTORE
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.PUSH32[
                0x994A936646FE87FFE4F1E469D3D6AA417D6B855598397F323DE5B449F765F0C3  # noqa: E501
            ]
            + Op.SWAP2
            + Op.SWAP1
            + Op.LOG1
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x377, condition=Op.ISZERO)
            + Op.PUSH2[0x38A]
            + Op.DUP3
            + Op.JUMP(pc=Op.PUSH2[0xBE])
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x395, condition=Op.ISZERO)
            + Op.POP
            + Op.JUMP(pc=0x379)
            + Op.JUMPDEST
            + Op.PUSH2[0x39D]
            + Op.JUMP(pc=0x2D9)
            + Op.JUMPDEST
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0xFA]
            + Op.SWAP1
            + Op.JUMPI(pc=0x3B4, condition=Op.ISZERO(Op.ISZERO(Op.LT)))
            + Op.PUSH2[0x3B2]
            + Op.JUMP(pc=0x3CB)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPDEST
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0xFA]
            + Op.SWAP1
            + Op.JUMPI(pc=0x3F5, condition=Op.ISZERO(Op.ISZERO(Op.LT)))
            + Op.POP
            + Op.JUMP(pc=0x379)
            + Op.JUMPDEST
            + Op.PUSH2[0x425]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6F7,
                condition=Op.ISZERO(Op.LT(Op.DUP2, Op.SLOAD(key=0x1))),
            )
            + Op.JUMPDEST
            + Op.LT(Op.DUP2, Op.SLOAD(key=0x1))
            + Op.JUMPI(pc=0x753, condition=Op.ISZERO(Op.DUP1))
            + Op.POP
            + Op.PUSH1[0x2]
            + Op.DUP2
            + Op.JUMPI(pc=0x74C, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.ADD(Op.DUP2, Op.SLOAD(key=Op.DUP1))
            + Op.SWAP1
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.SWAP1
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x31C, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x40]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.PUSH32[
                0x58619076ADF5BB0943D100EF88D52D7C3FD691B19D3A9071B555B651FBF418DA  # noqa: E501
            ]
            + Op.SWAP1
            + Op.PUSH1[0x20]
            + Op.SWAP1
            + Op.LOG1
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x281, condition=Op.ISZERO)
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
            + Op.SWAP3
            + Op.POP
            + Op.DUP3
            + Op.JUMPI(pc=0x4A8, condition=Op.ISZERO(Op.EQ))
            + Op.POP
            + Op.JUMP(pc=0x377)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x1]
            + Op.POP(0x0)
            + Op.SLOAD
            + Op.SUB
            + Op.PUSH1[0x0]
            + Op.POP(0x0)
            + Op.SLOAD
            + Op.JUMPI(pc=0x4C3, condition=Op.ISZERO(Op.GT))
            + Op.POP
            + Op.JUMP(pc=0x377)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x2]
            + Op.DUP4
            + Op.JUMPI(pc=0x4D3, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ADD
            + Op.SSTORE
            + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=0x102)
            + Op.SHA3(offset=Op.DUP2, size=0x40)
            + Op.SSTORE
            + Op.PUSH2[0x3C7]
            + Op.JUMP(pc=0x2D9)
            + Op.JUMPDEST
            + Op.PUSH1[0x40]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
            + Op.PUSH32[
                0xACBDB084C721332AC59F9B8E392196C9EB0E4932862DA8EB9BEAF0DAD4F550DA  # noqa: E501
            ]
            + Op.SWAP1
            + Op.PUSH1[0x20]
            + Op.SWAP1
            + Op.LOG1
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x377, condition=Op.ISZERO)
            + Op.JUMPI(
                pc=0x548,
                condition=Op.ISZERO(Op.GT(Op.DUP3, Op.SLOAD(key=0x1))),
            )
            + Op.POP
            + Op.JUMP(pc=0x379)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.SWAP1
            + Op.SSTORE
            + Op.PUSH2[0x504]
            + Op.JUMP(pc=0x2D9)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.DUP4,
                value=Op.ADD(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    Op.SLOAD(key=Op.DUP3),
                ),
            )
            + Op.ADD(Op.DUP4, 0x1)
            + Op.OR(Op.DUP3, Op.SLOAD(key=Op.DUP1))
            + Op.SWAP1
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.SWAP2
            + Op.SWAP1
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP7)
            + Op.MSTORE(offset=0x20, value=0x103)
            + Op.SHA3(offset=Op.DUP2, size=0x40)
            + Op.SLOAD(key=Op.DUP1)
            + Op.SWAP1
            + Op.SWAP5
            + Op.POP
            + Op.SWAP1
            + Op.SWAP3
            + Op.POP
            + Op.DUP3
            + Op.JUMPI(pc=0x61A, condition=Op.ISZERO(Op.EQ))
            + Op.SSTORE(key=Op.DUP4, value=Op.SLOAD(key=Op.DUP2))
            + Op.PUSH1[0x1]
            + Op.ADD(Op.DUP2, Op.DUP4)
            + Op.DUP4
            + Op.SWAP1
            + Op.SSTORE
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.SWAP2
            + Op.DUP3
            + Op.ADD
            + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
            + Op.DUP3
            + Op.ISZERO(Op.DUP1)
            + Op.DUP3
            + Op.SWAP1
            + Op.JUMPI(pc=0x6A6, condition=Op.GT)
            + Op.MSTORE(offset=Op.DUP7, value=Op.DUP3)
            + Op.PUSH32[
                0x4C0BE60200FAA20559308CB7B5A1BB3255C16CB1CAB91F525B5AE7A03D02FABE  # noqa: E501
            ]
            + Op.SWAP1
            + Op.DUP2
            + Op.ADD
            + Op.SWAP1
            + Op.DUP3
            + Op.ADD
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x6A4, condition=Op.ISZERO(Op.GT(Op.DUP3, Op.DUP1)))
            + Op.SSTORE(key=Op.DUP2, value=0x0)
            + Op.PUSH1[0x1]
            + Op.ADD
            + Op.JUMP(pc=0x5F9)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE
            + Op.PUSH1[0x20]
            + Op.SWAP1
            + Op.SWAP2
            + Op.SSTORE(key=Op.ADD, value=Op.SHA3)
            + Op.JUMPDEST
            + Op.POP
            + Op.SLOAD(key=Op.ADD(Op.DUP3, 0x1))
            + Op.PUSH1[0x2]
            + Op.DUP5
            + Op.SWAP1
            + Op.EXP
            + Op.SWAP1
            + Op.DUP2
            + Op.JUMPI(pc=0x586, condition=Op.ISZERO(Op.EQ(0x0, Op.AND)))
            + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.PUSH1[0x40]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.PUSH1[0x60]
            + Op.DUP8
            + Op.SWAP1
            + Op.MSTORE
            + Op.PUSH32[
                0xE1C52DC63B719ADE82E8BEA94CC41A0D5D28E4AAF536ADB5E9CCCC9FF8C1AEDA  # noqa: E501
            ]
            + Op.SWAP1
            + Op.DUP1
            + Op.LOG1
            + Op.SLOAD(key=Op.DUP3)
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.JUMPI(pc=0x555, condition=Op.ISZERO(Op.ISZERO(Op.GT)))
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP7)
            + Op.MSTORE(offset=0x20, value=0x103)
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.PUSH1[0x40]
            + Op.SWAP1
            + Op.SWAP3
            + Op.SLOAD(key=Op.ADD(0x2, Op.SHA3))
            + Op.SWAP1
            + Op.SWAP2
            + Op.DUP2
            + Op.JUMPI(pc=0x6C0, condition=Op.LT)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.ADD(Op.DUP5, 0x2)
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.DUP9
            + Op.SWAP3
            + Op.SWAP1
            + Op.DUP2
            + Op.JUMPI(pc=0x60D, condition=Op.LT)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE
            + Op.PUSH1[0x20]
            + Op.SHA3(offset=Op.DUP4, size=Op.DUP1)
            + Op.SWAP1
            + Op.SWAP2
            + Op.ADD
            + Op.DUP3
            + Op.SWAP1
            + Op.SSTORE
            + Op.MSTORE(offset=Op.DUP3, value=Op.DUP8)
            + Op.PUSH2[0x103]
            + Op.SWAP1
            + Op.MSTORE
            + Op.SHA3(offset=Op.DUP2, size=0x40)
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.PUSH1[0x1]
            + Op.ADD(Op.DUP2, Op.DUP2)
            + Op.DUP4
            + Op.SWAP1
            + Op.SSTORE
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.SWAP2
            + Op.ADD
            + Op.SWAP2
            + Op.SWAP1
            + Op.SWAP2
            + Op.SSTORE
            + Op.SWAP5
            + Op.POP
            + Op.JUMP(pc=0x586)
            + Op.JUMPDEST
            + Op.POP
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.EQ(0x0, Op.SLOAD(key=Op.ADD))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x760, condition=Op.ISZERO)
            + Op.PUSH1[0x1]
            + Op.ADD(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                Op.SLOAD(key=Op.DUP1),
            )
            + Op.SWAP1
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.GT(Op.SLOAD(key=Op.DUP1), 0x1)
            + Op.JUMPI(pc=0x701, condition=Op.ISZERO(Op.DUP1))
            + Op.POP
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x6FB, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ISZERO(Op.EQ(0x0, Op.SLOAD(key=Op.ADD)))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x72F, condition=Op.ISZERO)
            + Op.PUSH1[0x1]
            + Op.ADD
            + Op.JUMP(pc=0x3DB)
            + Op.JUMPDEST
            + Op.LT(Op.DUP2, Op.SLOAD(key=0x1))
            + Op.JUMPI(pc=0x784, condition=Op.ISZERO(Op.DUP1))
            + Op.POP
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x77D, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ISZERO(Op.EQ(0x0, Op.SLOAD(key=Op.ADD)))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x79F, condition=Op.ISZERO(Op.DUP1))
            + Op.POP
            + Op.PUSH1[0x2]
            + Op.DUP2
            + Op.JUMPI(pc=0x799, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.EQ(0x0, Op.SLOAD(key=Op.ADD))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x7B8, condition=Op.ISZERO)
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x7BD, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ADD
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMP(pc=0x3D0)
            + Op.JUMPDEST
            + Op.SLOAD(key=Op.ADD)
            + Op.PUSH1[0x2]
            + Op.DUP3
            + Op.JUMPI(pc=0x7CD, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.ADD
            + Op.SSTORE
            + Op.DUP1
            + Op.PUSH2[0x102]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x2]
            + Op.DUP4
            + Op.JUMPI(pc=0x7E3, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.MSTORE(offset=Op.DUP2, value=Op.SLOAD(key=Op.ADD))
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP2
            + Op.SWAP1
            + Op.SWAP2
            + Op.MSTORE
            + Op.PUSH1[0x40]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.SHA3
            + Op.SWAP2
            + Op.SWAP1
            + Op.SWAP2
            + Op.SSTORE
            + Op.SLOAD(key=0x1)
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x7B5, condition=Op.LT(Op.DUP2, 0x100))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP4, value=Op.DUP1)
            + Op.SWAP2
            + Op.SWAP1
            + Op.SWAP2
            + Op.MSTORE
            + Op.PUSH32[
                0x4C0BE60200FAA20559308CB7B5A1BB3255C16CB1CAB91F525B5AE7A03D02FABE  # noqa: E501
            ]
            + Op.SWAP1
            + Op.DUP2
            + Op.ADD
            + Op.SWAP1
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x27F, condition=Op.ISZERO(Op.GT(Op.DUP3, Op.DUP1)))
            + Op.SSTORE(key=Op.DUP2, value=0x0)
            + Op.PUSH1[0x1]
            + Op.ADD
            + Op.JUMP(pc=0x840)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x8A6,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.EQ(
                            Op.SLOAD(key=Op.ADD),
                            Op.SHA3(offset=Op.DUP3, size=0x20),
                        ),
                    ),
                ),
            )
            + Op.PUSH2[0x104]
            + Op.SLOAD(key=Op.DUP1)
            + Op.PUSH2[0x103]
            + Op.SWAP2
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.DUP5
            + Op.SWAP1
            + Op.DUP2
            + Op.JUMPI(pc=0x87C, condition=Op.LT)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE
            + Op.PUSH1[0x20]
            + Op.SHA3(offset=Op.DUP4, size=Op.DUP1)
            + Op.SWAP1
            + Op.SWAP2
            + Op.MSTORE(offset=Op.DUP4, value=Op.SLOAD(key=Op.ADD))
            + Op.DUP3
            + Op.ADD
            + Op.SWAP3
            + Op.SWAP1
            + Op.SWAP3
            + Op.MSTORE
            + Op.PUSH1[0x40]
            + Op.SHA3(offset=Op.DUP2, size=Op.ADD)
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x1)
            + Op.DUP3
            + Op.SWAP1
            + Op.SSTORE
            + Op.SSTORE(key=Op.ADD, value=0x2)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.ADD
            + Op.JUMP(pc=0x2E0)
        ),
        storage={
            0x0: 0x1,
            0x1: 0x2,
            0x3: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
            0x4: 0x3FB1CD2CD96C6D5C0B5EB3322D807B34482481D4,
            0x6E369836487C234B9E553EF3F787C2D8865520739D340C67B3D251A33986E58D: 0x1,  # noqa: E501
            0xD3E69D8C7F41F7AEAF8130DDC53047AEEE8CB46A73D6BAE86B7E7D6BF8312E6B: 0x2,  # noqa: E501
        },
        balance=100,
        nonce=0,
        address=Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A75EF08F, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "173825d9000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b"  # noqa: E501
        ),
        gas_limit=10000000,
        nonce=1,
        value=100,
    )

    post = {
        contract: Account(
            storage={
                0: 1,
                1: 1,
                3: 0x3FB1CD2CD96C6D5C0B5EB3322D807B34482481D4,
                0xD3E69D8C7F41F7AEAF8130DDC53047AEEE8CB46A73D6BAE86B7E7D6BF8312E6B: 1,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
