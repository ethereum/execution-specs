"""
Instruction Encoding (Opcodes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Machine readable representations of EVM instructions, and a mapping to their
implementations.
"""

from typing import Callable, Dict

from . import instructions

# Arithmetic Operations
STOP = 0x00
ADD = 0x01
MUL = 0x02
SUB = 0x03
DIV = 0x04
SDIV = 0x05
MOD = 0x06
SMOD = 0x07
ADDMOD = 0x08
MULMOD = 0x09
EXP = 0x0A
SIGNEXTEND = 0x0B

# Push Operations
PUSH1 = 0x60
PUSH2 = 0x61
PUSH3 = 0x62
PUSH4 = 0x63
PUSH5 = 0x64
PUSH6 = 0x65
PUSH7 = 0x66
PUSH8 = 0x67
PUSH9 = 0x68
PUSH10 = 0x69
PUSH11 = 0x6A
PUSH12 = 0x6B
PUSH13 = 0x6C
PUSH14 = 0x6D
PUSH15 = 0x6E
PUSH16 = 0x6F
PUSH17 = 0x70
PUSH18 = 0x71
PUSH19 = 0x72
PUSH20 = 0x73
PUSH21 = 0x74
PUSH22 = 0x75
PUSH23 = 0x76
PUSH24 = 0x77
PUSH25 = 0x78
PUSH26 = 0x79
PUSH27 = 0x7A
PUSH28 = 0x7B
PUSH29 = 0x7C
PUSH30 = 0x7D
PUSH31 = 0x7E
PUSH32 = 0x7F

SSTORE = 0x55


op_implementation: Dict[int, Callable] = {
    STOP: instructions.stop,
    ADD: instructions.add,
    MUL: instructions.mul,
    SUB: instructions.sub,
    DIV: instructions.div,
    SDIV: instructions.sdiv,
    MOD: instructions.mod,
    SMOD: instructions.smod,
    ADDMOD: instructions.addmod,
    MULMOD: instructions.mulmod,
    EXP: instructions.exp,
    SIGNEXTEND: instructions.signextend,
    SSTORE: instructions.sstore,
    PUSH1: instructions.push1,
    PUSH2: instructions.push2,
    PUSH3: instructions.push3,
    PUSH4: instructions.push4,
    PUSH5: instructions.push5,
    PUSH6: instructions.push6,
    PUSH7: instructions.push7,
    PUSH8: instructions.push8,
    PUSH9: instructions.push9,
    PUSH10: instructions.push10,
    PUSH11: instructions.push11,
    PUSH12: instructions.push12,
    PUSH13: instructions.push13,
    PUSH14: instructions.push14,
    PUSH15: instructions.push15,
    PUSH16: instructions.push16,
    PUSH17: instructions.push17,
    PUSH18: instructions.push18,
    PUSH19: instructions.push19,
    PUSH20: instructions.push20,
    PUSH21: instructions.push21,
    PUSH22: instructions.push22,
    PUSH23: instructions.push23,
    PUSH24: instructions.push24,
    PUSH25: instructions.push25,
    PUSH26: instructions.push26,
    PUSH27: instructions.push27,
    PUSH28: instructions.push28,
    PUSH29: instructions.push29,
    PUSH30: instructions.push30,
    PUSH31: instructions.push31,
    PUSH32: instructions.push32,
}
