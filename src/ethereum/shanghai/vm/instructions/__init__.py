"""
EVM Instruction Encoding (Opcodes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Machine readable representations of EVM instructions, and a mapping to their
implementations.
"""

import enum
from typing import Callable, Dict

from . import arithmetic as arithmetic_instructions
from . import bitwise as bitwise_instructions
from . import block as block_instructions
from . import comparison as comparison_instructions
from . import control_flow as control_flow_instructions
from . import environment as environment_instructions
from . import keccak as keccak_instructions
from . import log as log_instructions
from . import memory as memory_instructions
from . import stack as stack_instructions
from . import storage as storage_instructions
from . import system as system_instructions


class Ops(enum.Enum):
    """
    Enum for EVM Opcodes
    """

    # Arithmetic Ops
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

    # Comparison Ops
    LT = 0x10
    GT = 0x11
    SLT = 0x12
    SGT = 0x13
    EQ = 0x14
    ISZERO = 0x15

    # Bitwise Ops
    AND = 0x16
    OR = 0x17
    XOR = 0x18
    NOT = 0x19
    BYTE = 0x1A
    SHL = 0x1B
    SHR = 0x1C
    SAR = 0x1D

    # Keccak Op
    KECCAK = 0x20

    # Environmental Ops
    ADDRESS = 0x30
    BALANCE = 0x31
    ORIGIN = 0x32
    CALLER = 0x33
    CALLVALUE = 0x34
    CALLDATALOAD = 0x35
    CALLDATASIZE = 0x36
    CALLDATACOPY = 0x37
    CODESIZE = 0x38
    CODECOPY = 0x39
    GASPRICE = 0x3A
    EXTCODESIZE = 0x3B
    EXTCODECOPY = 0x3C
    RETURNDATASIZE = 0x3D
    RETURNDATACOPY = 0x3E
    EXTCODEHASH = 0x3F

    # Block Ops
    BLOCKHASH = 0x40
    COINBASE = 0x41
    TIMESTAMP = 0x42
    NUMBER = 0x43
    PREVRANDAO = 0x44
    GASLIMIT = 0x45
    CHAINID = 0x46
    SELFBALANCE = 0x47
    BASEFEE = 0x48

    # Control Flow Ops
    STOP = 0x00
    JUMP = 0x56
    JUMPI = 0x57
    PC = 0x58
    GAS = 0x5A
    JUMPDEST = 0x5B

    # Storage Ops
    SLOAD = 0x54
    SSTORE = 0x55

    # Pop Operation
    POP = 0x50

    # Push Operations
    PUSH0 = 0x5F
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

    # Memory Operations
    MLOAD = 0x51
    MSTORE = 0x52
    MSTORE8 = 0x53
    MSIZE = 0x59

    # Log Operations
    LOG0 = 0xA0
    LOG1 = 0xA1
    LOG2 = 0xA2
    LOG3 = 0xA3
    LOG4 = 0xA4

    # System Operations
    CREATE = 0xF0
    RETURN = 0xF3
    CALL = 0xF1
    CALLCODE = 0xF2
    DELEGATECALL = 0xF4
    STATICCALL = 0xFA
    REVERT = 0xFD
    SELFDESTRUCT = 0xFF
    CREATE2 = 0xF5


op_implementation: Dict[Ops, Callable] = {
    Ops.STOP: control_flow_instructions.stop,
    Ops.ADD: arithmetic_instructions.add,
    Ops.MUL: arithmetic_instructions.mul,
    Ops.SUB: arithmetic_instructions.sub,
    Ops.DIV: arithmetic_instructions.div,
    Ops.SDIV: arithmetic_instructions.sdiv,
    Ops.MOD: arithmetic_instructions.mod,
    Ops.SMOD: arithmetic_instructions.smod,
    Ops.ADDMOD: arithmetic_instructions.addmod,
    Ops.MULMOD: arithmetic_instructions.mulmod,
    Ops.EXP: arithmetic_instructions.exp,
    Ops.SIGNEXTEND: arithmetic_instructions.signextend,
    Ops.LT: comparison_instructions.less_than,
    Ops.GT: comparison_instructions.greater_than,
    Ops.SLT: comparison_instructions.signed_less_than,
    Ops.SGT: comparison_instructions.signed_greater_than,
    Ops.EQ: comparison_instructions.equal,
    Ops.ISZERO: comparison_instructions.is_zero,
    Ops.AND: bitwise_instructions.bitwise_and,
    Ops.OR: bitwise_instructions.bitwise_or,
    Ops.XOR: bitwise_instructions.bitwise_xor,
    Ops.NOT: bitwise_instructions.bitwise_not,
    Ops.BYTE: bitwise_instructions.get_byte,
    Ops.SHL: bitwise_instructions.bitwise_shl,
    Ops.SHR: bitwise_instructions.bitwise_shr,
    Ops.SAR: bitwise_instructions.bitwise_sar,
    Ops.KECCAK: keccak_instructions.keccak,
    Ops.SLOAD: storage_instructions.sload,
    Ops.BLOCKHASH: block_instructions.block_hash,
    Ops.COINBASE: block_instructions.coinbase,
    Ops.TIMESTAMP: block_instructions.timestamp,
    Ops.NUMBER: block_instructions.number,
    Ops.PREVRANDAO: block_instructions.prev_randao,
    Ops.GASLIMIT: block_instructions.gas_limit,
    Ops.CHAINID: block_instructions.chain_id,
    Ops.MLOAD: memory_instructions.mload,
    Ops.MSTORE: memory_instructions.mstore,
    Ops.MSTORE8: memory_instructions.mstore8,
    Ops.MSIZE: memory_instructions.msize,
    Ops.ADDRESS: environment_instructions.address,
    Ops.BALANCE: environment_instructions.balance,
    Ops.ORIGIN: environment_instructions.origin,
    Ops.CALLER: environment_instructions.caller,
    Ops.CALLVALUE: environment_instructions.callvalue,
    Ops.CALLDATALOAD: environment_instructions.calldataload,
    Ops.CALLDATASIZE: environment_instructions.calldatasize,
    Ops.CALLDATACOPY: environment_instructions.calldatacopy,
    Ops.CODESIZE: environment_instructions.codesize,
    Ops.CODECOPY: environment_instructions.codecopy,
    Ops.GASPRICE: environment_instructions.gasprice,
    Ops.EXTCODESIZE: environment_instructions.extcodesize,
    Ops.EXTCODECOPY: environment_instructions.extcodecopy,
    Ops.RETURNDATASIZE: environment_instructions.returndatasize,
    Ops.RETURNDATACOPY: environment_instructions.returndatacopy,
    Ops.EXTCODEHASH: environment_instructions.extcodehash,
    Ops.SELFBALANCE: environment_instructions.self_balance,
    Ops.BASEFEE: environment_instructions.base_fee,
    Ops.SSTORE: storage_instructions.sstore,
    Ops.JUMP: control_flow_instructions.jump,
    Ops.JUMPI: control_flow_instructions.jumpi,
    Ops.PC: control_flow_instructions.pc,
    Ops.GAS: control_flow_instructions.gas_left,
    Ops.JUMPDEST: control_flow_instructions.jumpdest,
    Ops.POP: stack_instructions.pop,
    Ops.PUSH0: stack_instructions.push0,
    Ops.PUSH1: stack_instructions.push1,
    Ops.PUSH2: stack_instructions.push2,
    Ops.PUSH3: stack_instructions.push3,
    Ops.PUSH4: stack_instructions.push4,
    Ops.PUSH5: stack_instructions.push5,
    Ops.PUSH6: stack_instructions.push6,
    Ops.PUSH7: stack_instructions.push7,
    Ops.PUSH8: stack_instructions.push8,
    Ops.PUSH9: stack_instructions.push9,
    Ops.PUSH10: stack_instructions.push10,
    Ops.PUSH11: stack_instructions.push11,
    Ops.PUSH12: stack_instructions.push12,
    Ops.PUSH13: stack_instructions.push13,
    Ops.PUSH14: stack_instructions.push14,
    Ops.PUSH15: stack_instructions.push15,
    Ops.PUSH16: stack_instructions.push16,
    Ops.PUSH17: stack_instructions.push17,
    Ops.PUSH18: stack_instructions.push18,
    Ops.PUSH19: stack_instructions.push19,
    Ops.PUSH20: stack_instructions.push20,
    Ops.PUSH21: stack_instructions.push21,
    Ops.PUSH22: stack_instructions.push22,
    Ops.PUSH23: stack_instructions.push23,
    Ops.PUSH24: stack_instructions.push24,
    Ops.PUSH25: stack_instructions.push25,
    Ops.PUSH26: stack_instructions.push26,
    Ops.PUSH27: stack_instructions.push27,
    Ops.PUSH28: stack_instructions.push28,
    Ops.PUSH29: stack_instructions.push29,
    Ops.PUSH30: stack_instructions.push30,
    Ops.PUSH31: stack_instructions.push31,
    Ops.PUSH32: stack_instructions.push32,
    Ops.DUP1: stack_instructions.dup1,
    Ops.DUP2: stack_instructions.dup2,
    Ops.DUP3: stack_instructions.dup3,
    Ops.DUP4: stack_instructions.dup4,
    Ops.DUP5: stack_instructions.dup5,
    Ops.DUP6: stack_instructions.dup6,
    Ops.DUP7: stack_instructions.dup7,
    Ops.DUP8: stack_instructions.dup8,
    Ops.DUP9: stack_instructions.dup9,
    Ops.DUP10: stack_instructions.dup10,
    Ops.DUP11: stack_instructions.dup11,
    Ops.DUP12: stack_instructions.dup12,
    Ops.DUP13: stack_instructions.dup13,
    Ops.DUP14: stack_instructions.dup14,
    Ops.DUP15: stack_instructions.dup15,
    Ops.DUP16: stack_instructions.dup16,
    Ops.SWAP1: stack_instructions.swap1,
    Ops.SWAP2: stack_instructions.swap2,
    Ops.SWAP3: stack_instructions.swap3,
    Ops.SWAP4: stack_instructions.swap4,
    Ops.SWAP5: stack_instructions.swap5,
    Ops.SWAP6: stack_instructions.swap6,
    Ops.SWAP7: stack_instructions.swap7,
    Ops.SWAP8: stack_instructions.swap8,
    Ops.SWAP9: stack_instructions.swap9,
    Ops.SWAP10: stack_instructions.swap10,
    Ops.SWAP11: stack_instructions.swap11,
    Ops.SWAP12: stack_instructions.swap12,
    Ops.SWAP13: stack_instructions.swap13,
    Ops.SWAP14: stack_instructions.swap14,
    Ops.SWAP15: stack_instructions.swap15,
    Ops.SWAP16: stack_instructions.swap16,
    Ops.LOG0: log_instructions.log0,
    Ops.LOG1: log_instructions.log1,
    Ops.LOG2: log_instructions.log2,
    Ops.LOG3: log_instructions.log3,
    Ops.LOG4: log_instructions.log4,
    Ops.CREATE: system_instructions.create,
    Ops.RETURN: system_instructions.return_,
    Ops.CALL: system_instructions.call,
    Ops.CALLCODE: system_instructions.callcode,
    Ops.DELEGATECALL: system_instructions.delegatecall,
    Ops.SELFDESTRUCT: system_instructions.selfdestruct,
    Ops.STATICCALL: system_instructions.staticcall,
    Ops.REVERT: system_instructions.revert,
    Ops.CREATE2: system_instructions.create2,
}
