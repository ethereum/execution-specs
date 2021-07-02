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

# Dup operations
DUP1 = 0x80
DUP2 = 0x81
DUP3 = 0x82
DUP4 = 0x83
DUP5 = 0x84
DUP6 = 0x85
DUP7 = 0x86
DUP8 = 0x87
DUP9 = 0x88
DUP10 = 0x89
DUP11 = 0x8A
DUP12 = 0x8B
DUP13 = 0x8C
DUP14 = 0x8D
DUP15 = 0x8E
DUP16 = 0x8F

# Swap operations
SWAP1 = 0x90
SWAP2 = 0x91
SWAP3 = 0x92
SWAP4 = 0x93
SWAP5 = 0x94
SWAP6 = 0x95
SWAP7 = 0x96
SWAP8 = 0x97
SWAP9 = 0x98
SWAP10 = 0x99
SWAP11 = 0x9A
SWAP12 = 0x9B
SWAP13 = 0x9C
SWAP14 = 0x9D
SWAP15 = 0x9E
SWAP16 = 0x9F

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
    DUP1: instructions.dup1,
    DUP2: instructions.dup2,
    DUP3: instructions.dup3,
    DUP4: instructions.dup4,
    DUP5: instructions.dup5,
    DUP6: instructions.dup6,
    DUP7: instructions.dup7,
    DUP8: instructions.dup8,
    DUP9: instructions.dup9,
    DUP10: instructions.dup10,
    DUP11: instructions.dup11,
    DUP12: instructions.dup12,
    DUP13: instructions.dup13,
    DUP14: instructions.dup14,
    DUP15: instructions.dup15,
    DUP16: instructions.dup16,
    SWAP1: instructions.swap1,
    SWAP2: instructions.swap2,
    SWAP3: instructions.swap3,
    SWAP4: instructions.swap4,
    SWAP5: instructions.swap5,
    SWAP6: instructions.swap6,
    SWAP7: instructions.swap7,
    SWAP8: instructions.swap8,
    SWAP9: instructions.swap9,
    SWAP10: instructions.swap10,
    SWAP11: instructions.swap11,
    SWAP12: instructions.swap12,
    SWAP13: instructions.swap13,
    SWAP14: instructions.swap14,
    SWAP15: instructions.swap15,
    SWAP16: instructions.swap16,
}
