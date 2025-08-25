"""Define a program for scenario test that executes all frontier opcodes and entangles it's result."""  # noqa: E501

from functools import cached_property

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Bytecode, Conditional
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ..common import ProgramResult, ScenarioTestProgram

# Opcodes that are not in Frontier
# 1b - SHL
# 1c - SHR
# 1d - SAR


def make_all_opcode_program() -> Bytecode:
    """Make a program that call each Frontier opcode and verifies it's result."""
    code: Bytecode = (
        # Test opcode 01 - ADD
        Conditional(
            condition=Op.EQ(Op.ADD(1, 1), 2),
            if_true=Op.MSTORE(0, 2),
            if_false=Op.MSTORE(0, 0) + Op.RETURN(0, 32),
        )
        # Test opcode 02 - MUL
        + Conditional(
            condition=Op.EQ(
                Op.MUL(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 2),
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 2) + Op.RETURN(0, 32),
        )
        # Test 03 - SUB
        + Conditional(
            condition=Op.EQ(
                Op.SUB(0, 1),
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 3) + Op.RETURN(0, 32),
        )
        # Test 04 - DIV
        + Conditional(
            condition=Op.AND(Op.EQ(Op.DIV(1, 2), 0), Op.EQ(Op.DIV(10, 2), 5)),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 4) + Op.RETURN(0, 32),
        )
        # Test 05 - SDIV
        + Conditional(
            condition=Op.EQ(
                Op.SDIV(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                2,
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 5) + Op.RETURN(0, 32),
        )
        # Test 06 - MOD
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.MOD(10, 3), 1),
                Op.EQ(
                    Op.MOD(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF8,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD,
                    ),
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF8,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 6) + Op.RETURN(0, 32),
        )
        # Test 07 - SMOD
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.SMOD(10, 3), 1),
                Op.EQ(
                    Op.SMOD(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF8,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD,
                    ),
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 7) + Op.RETURN(0, 32),
        )
        # Test 08 - ADDMOD
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.ADDMOD(10, 10, 8), 4),
                Op.EQ(
                    Op.ADDMOD(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                        2,
                        2,
                    ),
                    1,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 8) + Op.RETURN(0, 32),
        )
        # Test 09 - MULMOD
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.MULMOD(10, 10, 8), 4),
                Op.EQ(
                    Op.MULMOD(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                        12,
                    ),
                    9,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 9) + Op.RETURN(0, 32),
        )
        # Test 0A - EXP
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.EXP(10, 2), 100),
                Op.EQ(
                    Op.EXP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD, 2),
                    9,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 10) + Op.RETURN(0, 32),
        )
        # Test 0B - SIGNEXTEND
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.SIGNEXTEND(0, 0xFF),
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                Op.EQ(
                    Op.SIGNEXTEND(0, 0x7F),
                    0x7F,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 11) + Op.RETURN(0, 32),
        )
        # Test 10 - LT
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.LT(9, 10),
                    1,
                ),
                Op.EQ(
                    Op.LT(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0),
                    0,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x10) + Op.RETURN(0, 32),
        )
        # Test 11 - GT
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.GT(9, 10),
                    0,
                ),
                Op.EQ(
                    Op.GT(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0),
                    1,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x11) + Op.RETURN(0, 32),
        )
        # Test 12 - SLT
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.SLT(9, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                    0,
                ),
                Op.EQ(
                    Op.SLT(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0),
                    1,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x12) + Op.RETURN(0, 32),
        )
        # Test 13 - SGT
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.SGT(10, 10),
                    0,
                ),
                Op.EQ(
                    Op.SGT(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                    1,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x13) + Op.RETURN(0, 32),
        )
        # Test 14 - EQ Skip
        # Test 15 - ISZero
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.ISZERO(10), 0),
                Op.EQ(Op.ISZERO(0), 1),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x15) + Op.RETURN(0, 32),
        )
        # Test 16 - AND Skip
        # Test 17 - OR
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.OR(0xF0, 0xF), 0xFF),
                Op.EQ(Op.OR(0xFF, 0xFF), 0xFF),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x17) + Op.RETURN(0, 32),
        )
        # Test 18 - XOR
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.XOR(0xF0, 0xF), 0xFF),
                Op.EQ(Op.XOR(0xFF, 0xFF), 0),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x18) + Op.RETURN(0, 32),
        )
        # Test 19 - NOT
        + Conditional(
            condition=Op.AND(
                Op.EQ(
                    Op.NOT(0), 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                ),
                Op.EQ(
                    Op.NOT(0xFFFFFFFFFFFF),
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000,
                ),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x19) + Op.RETURN(0, 32),
        )
        # Test 1A - BYTE
        + Conditional(
            condition=Op.AND(
                Op.EQ(Op.BYTE(31, 0xFF), 0xFF),
                Op.EQ(Op.BYTE(30, 0xFF00), 0xFF),
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x1A) + Op.RETURN(0, 32),
        )
        # Test 20 - SHA3
        + Op.MSTORE(0, 0xFFFFFFFF)
        + Conditional(
            condition=Op.EQ(
                Op.SHA3(28, 4),
                0x29045A592007D0C246EF02C2223570DA9522D0CF0F73282C79A1BC8F0BB2C238,
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x20) + Op.RETURN(0, 32),
        )
        # 50 POP
        # 51 MLOAD
        # 52 MSTORE
        # 53 MSTORE8
        + Op.MSTORE(0, 0)
        + Op.MSTORE8(0, 0xFFFF)
        + Conditional(
            condition=Op.EQ(
                Op.MLOAD(0),
                0xFF00000000000000000000000000000000000000000000000000000000000000,
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x53) + Op.RETURN(0, 32),
        )
        # 54 SLOAD
        + Conditional(
            condition=Op.EQ(Op.SLOAD(0), 0),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x54) + Op.RETURN(0, 32),
        )
        # 55 SSTORE # can't use because of static contexts
        # 56 JUMP
        # 57 JUMPI
        # 58 PC
        + Conditional(
            condition=Op.EQ(Op.PC, 1660),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x58) + Op.RETURN(0, 32),
        )
        # 59 MSIZE
        + Op.MSTORE(64, 123)
        + Conditional(
            condition=Op.EQ(Op.MSIZE, 96),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x59) + Op.RETURN(0, 32),
        )
        # 5A GAS
        # 5B JUMPDEST
        # 5C TLOAD
        # 5D TSTORE # can't use because of static contexts
        # 5E MCOPY
        # 5F PUSH0
        # 60 - 7F  PUSH X
        + Op.PUSH1(0xFF)
        + Op.PUSH2(0xFFFF)
        + Op.ADD
        + Op.PUSH3(0xFFFFFF)
        + Op.ADD
        + Op.PUSH4(0xFFFFFFFF)
        + Op.ADD
        + Op.PUSH5(0xFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH6(0xFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH7(0xFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH8(0xFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH9(0xFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH10(0xFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH11(0xFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH12(0xFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH13(0xFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH14(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH15(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH16(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH17(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH18(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH19(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH20(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH21(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH22(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH23(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH24(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH25(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH26(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH27(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH28(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH29(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH30(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH31(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH32(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.ADD
        + Op.PUSH1(0)
        + Op.MSTORE
        + Conditional(
            condition=Op.EQ(
                Op.MLOAD(0), 0x1010101010101010101010101010101010101010101010101010101010100E0
            ),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 60) + Op.RETURN(0, 32),
        )
        # 80 - 8F  DUP X
        + Op.PUSH1(1)
        + Op.DUP1
        + Op.DUP2
        + Op.DUP3
        + Op.DUP4
        + Op.DUP5
        + Op.DUP6
        + Op.DUP7
        + Op.DUP8
        + Op.DUP9
        + Op.DUP10
        + Op.DUP11
        + Op.DUP12
        + Op.DUP13
        + Op.DUP14
        + Op.DUP15
        + Op.DUP16
        + Op.ADD * 16
        + Op.PUSH1(0)
        + Op.MSTORE
        + Conditional(
            condition=Op.EQ(Op.MLOAD(0), 17),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x80) + Op.RETURN(0, 32),
        )
        # 90 - 9F SWAP X
        + Op.PUSH1(3)
        + Op.PUSH1(5)
        + Op.SWAP1
        + Op.PUSH1(7)
        + Op.SWAP2
        + Op.PUSH1(11)
        + Op.SWAP3
        + Op.PUSH1(13)
        + Op.SWAP4
        + Op.PUSH1(17)
        + Op.SWAP5
        + Op.PUSH1(19)
        + Op.SWAP6
        + Op.PUSH1(23)
        + Op.SWAP7
        + Op.PUSH1(29)
        + Op.SWAP8
        + Op.PUSH1(31)
        + Op.SWAP9
        + Op.PUSH1(37)
        + Op.SWAP10
        + Op.PUSH1(41)
        + Op.SWAP11
        + Op.PUSH1(43)
        + Op.SWAP12
        + Op.PUSH1(47)
        + Op.SWAP13
        + Op.PUSH1(53)
        + Op.SWAP14
        + Op.PUSH1(59)
        + Op.SWAP15
        + Op.PUSH1(61)
        + Op.SWAP16
        + Op.PUSH1(0)
        + Op.MSTORE
        + Conditional(
            condition=Op.EQ(Op.MLOAD(0), 59),
            if_true=Op.JUMPDEST,
            if_false=Op.MSTORE(0, 0x90) + Op.RETURN(0, 32),
        )
        # A0 - A4 LOG X - can't use because non static
        # F0 CREATE
        # F1 CALL
        # F2 CALLCODE
        # F3 RETURN
        # F4 DELEGATECALL
        # F5 CREATE2
        # FA STATICCALL
        # FD REVERT
        # FE INVALID
        # FF SELFDESTRUCT
        + Op.MSTORE(0, 1)
        + Op.RETURN(0, 32)
    )
    return code


class ProgramAllFrontierOpcodes(ScenarioTestProgram):
    """Check every frontier opcode functions."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return make_all_opcode_program()

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_ALL_FRONTIER_OPCODES"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1)
