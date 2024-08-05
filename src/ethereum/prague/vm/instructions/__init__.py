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
    RETURNDATALOAD = 0xF7
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
    BLOBHASH = 0x49
    BLOBBASEFEE = 0x4A

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
    TLOAD = 0x5C
    TSTORE = 0x5D

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
    MCOPY = 0x5E

    # Log Operations
    LOG0 = 0xA0
    LOG1 = 0xA1
    LOG2 = 0xA2
    LOG3 = 0xA3
    LOG4 = 0xA4

    # EOF Data section operations
    DATALOAD = 0xD0
    DATALOADN = 0xD1
    DATASIZE = 0xD2
    DATACOPY = 0xD3

    # Static Relative Jumps
    RJUMP = 0xE0
    RJUMPI = 0xE1
    RJUMPV = 0xE2

    # EOF Function Opcodes
    CALLF = 0xE3
    RETF = 0xE4
    JUMPF = 0xE5

    # EOF Stack Operations
    DUPN = 0xE6
    SWAPN = 0xE7
    EXCHANGE = 0xE8

    # System Operations
    EOFCREATE = 0xEC
    RETURNCONTRACT = 0xEE
    CREATE = 0xF0
    CALL = 0xF1
    CALLCODE = 0xF2
    RETURN = 0xF3
    DELEGATECALL = 0xF4
    CREATE2 = 0xF5
    EXTCALL = 0xF8
    EXTDELEGATECALL = 0xF9
    STATICCALL = 0xFA
    EXTSTATICCALL = 0xFB
    REVERT = 0xFD
    INVALID = 0xFE
    SELFDESTRUCT = 0xFF


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
    Ops.MCOPY: memory_instructions.mcopy,
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
    Ops.RETURNDATALOAD: environment_instructions.returndataload,
    Ops.EXTCODEHASH: environment_instructions.extcodehash,
    Ops.SELFBALANCE: environment_instructions.self_balance,
    Ops.BASEFEE: environment_instructions.base_fee,
    Ops.BLOBHASH: environment_instructions.blob_hash,
    Ops.BLOBBASEFEE: environment_instructions.blob_base_fee,
    Ops.SSTORE: storage_instructions.sstore,
    Ops.TLOAD: storage_instructions.tload,
    Ops.TSTORE: storage_instructions.tstore,
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
    Ops.DATALOAD: environment_instructions.dataload,
    Ops.DATALOADN: environment_instructions.dataload_n,
    Ops.DATASIZE: environment_instructions.datasize,
    Ops.DATACOPY: environment_instructions.datacopy,
    Ops.RJUMP: control_flow_instructions.rjump,
    Ops.RJUMPI: control_flow_instructions.rjumpi,
    Ops.RJUMPV: control_flow_instructions.rjumpv,
    Ops.CALLF: control_flow_instructions.callf,
    Ops.RETF: control_flow_instructions.retf,
    Ops.CREATE: system_instructions.create,
    Ops.RETURN: system_instructions.return_,
    Ops.CALL: system_instructions.call,
    Ops.CALLCODE: system_instructions.callcode,
    Ops.DELEGATECALL: system_instructions.delegatecall,
    Ops.SELFDESTRUCT: system_instructions.selfdestruct,
    Ops.STATICCALL: system_instructions.staticcall,
    Ops.REVERT: system_instructions.revert,
    Ops.INVALID: system_instructions.invalid,
    Ops.CREATE2: system_instructions.create2,
    Ops.EXTCALL: system_instructions.ext_call,
    Ops.EXTDELEGATECALL: system_instructions.ext_delegatecall,
    Ops.EXTSTATICCALL: system_instructions.ext_staticcall,
}


OPCODES_INVALID_IN_LEGACY = (
    Ops.INVALID,
    # Relative Jump instructions
    Ops.RJUMP,
    Ops.RJUMPI,
    Ops.RJUMPV,
    # EOF Data section operations
    Ops.DATALOAD,
    Ops.DATALOADN,
    Ops.DATASIZE,
    Ops.DATACOPY,
    # EOF Function Opcodes
    Ops.CALLF,
    Ops.RETF,
    Ops.JUMPF,
    # EOF Stack Operations
    Ops.DUPN,
    Ops.SWAPN,
    Ops.EXCHANGE,
    # System Operations
    Ops.EOFCREATE,
    Ops.RETURNDATALOAD,
    Ops.EXTCALL,
    Ops.EXTDELEGATECALL,
    Ops.EXTSTATICCALL,
    Ops.RETURNCONTRACT,
)

OPCODES_INVALID_IN_EOF1 = (
    # Environmental Ops
    Ops.CODESIZE,
    Ops.CODECOPY,
    Ops.EXTCODESIZE,
    Ops.EXTCODECOPY,
    Ops.EXTCODEHASH,
    # Control Flow Ops
    Ops.JUMP,
    Ops.JUMPI,
    Ops.PC,
    Ops.GAS,
    # System Operations
    Ops.CREATE,
    Ops.CALL,
    Ops.CALLCODE,
    Ops.DELEGATECALL,
    Ops.CREATE2,
    Ops.STATICCALL,
    Ops.SELFDESTRUCT,
)


op_stack_items: Dict[Ops, Callable] = {
    Ops.STOP: control_flow_instructions.STACK_STOP,
    Ops.ADD: arithmetic_instructions.STACK_ADD,
    Ops.MUL: arithmetic_instructions.STACK_MUL,
    Ops.SUB: arithmetic_instructions.STACK_SUB,
    Ops.DIV: arithmetic_instructions.STACK_DIV,
    Ops.SDIV: arithmetic_instructions.STACK_SDIV,
    Ops.MOD: arithmetic_instructions.STACK_MOD,
    Ops.SMOD: arithmetic_instructions.STACK_SMOD,
    Ops.ADDMOD: arithmetic_instructions.STACK_ADDMOD,
    Ops.MULMOD: arithmetic_instructions.STACK_MULMOD,
    Ops.EXP: arithmetic_instructions.STACK_EXP,
    Ops.SIGNEXTEND: arithmetic_instructions.STACK_SIGNEXTEND,
    Ops.LT: comparison_instructions.STACK_LESS_THAN,
    Ops.GT: comparison_instructions.STACK_GREATER_THAN,
    Ops.SLT: comparison_instructions.STACK_SIGNED_LESS_THAN,
    Ops.SGT: comparison_instructions.STACK_SIGNED_GREATER_THAN,
    Ops.EQ: comparison_instructions.STACK_EQUAL,
    Ops.ISZERO: comparison_instructions.STACK_IS_ZERO,
    Ops.AND: bitwise_instructions.STACK_BITWISE_AND,
    Ops.OR: bitwise_instructions.STACK_BITWISE_OR,
    Ops.XOR: bitwise_instructions.STACK_BITWISE_XOR,
    Ops.NOT: bitwise_instructions.STACK_BITWISE_NOT,
    Ops.BYTE: bitwise_instructions.STACK_GET_BYTE,
    Ops.SHL: bitwise_instructions.STACK_BITWISE_SHL,
    Ops.SHR: bitwise_instructions.STACK_BITWISE_SHR,
    Ops.SAR: bitwise_instructions.STACK_BITWISE_SAR,
    Ops.KECCAK: keccak_instructions.STACK_KECCAK,
    Ops.SLOAD: storage_instructions.STACK_SLOAD,
    Ops.BLOCKHASH: block_instructions.STACK_BLOCKHASH,
    Ops.COINBASE: block_instructions.STACK_COINBASE,
    Ops.TIMESTAMP: block_instructions.STACK_TIMESTAMP,
    Ops.NUMBER: block_instructions.STACK_NUMBER,
    Ops.PREVRANDAO: block_instructions.STACK_PREV_RANDAO,
    Ops.GASLIMIT: block_instructions.STACK_GAS_LIMIT,
    Ops.CHAINID: block_instructions.STACK_CHAIN_ID,
    Ops.MLOAD: memory_instructions.STACK_MLOAD,
    Ops.MSTORE: memory_instructions.STACK_MSTORE,
    Ops.MSTORE8: memory_instructions.STACK_MSTORE8,
    Ops.MSIZE: memory_instructions.STACK_MSIZE,
    Ops.MCOPY: memory_instructions.STACK_MCOPY,
    Ops.ADDRESS: environment_instructions.STACK_ADDRESS,
    Ops.BALANCE: environment_instructions.STACK_BALANCE,
    Ops.ORIGIN: environment_instructions.STACK_ORIGIN,
    Ops.CALLER: environment_instructions.STACK_CALLER,
    Ops.CALLVALUE: environment_instructions.STACK_CALLVALUE,
    Ops.CALLDATALOAD: environment_instructions.STACK_CALLDATALOAD,
    Ops.CALLDATASIZE: environment_instructions.STACK_CALLDATASIZE,
    Ops.CALLDATACOPY: environment_instructions.STACK_CALLDATACOPY,
    Ops.CODESIZE: environment_instructions.STACK_CODESIZE,
    Ops.CODECOPY: environment_instructions.STACK_CODECOPY,
    Ops.GASPRICE: environment_instructions.STACK_GASPRICE,
    Ops.EXTCODESIZE: environment_instructions.STACK_EXTCODESIZE,
    Ops.EXTCODECOPY: environment_instructions.STACK_EXTCODECOPY,
    Ops.RETURNDATASIZE: environment_instructions.STACK_RETURNDATASIZE,
    Ops.RETURNDATACOPY: environment_instructions.STACK_RETURNDATACOPY,
    Ops.RETURNDATALOAD: environment_instructions.STACK_RETURNDATALOAD,
    Ops.EXTCODEHASH: environment_instructions.STACK_EXTCODEHASH,
    Ops.SELFBALANCE: environment_instructions.STACK_SELF_BALANCE,
    Ops.BASEFEE: environment_instructions.STACK_BASE_FEE,
    Ops.BLOBHASH: environment_instructions.STACK_BLOB_HASH,
    Ops.BLOBBASEFEE: environment_instructions.STACK_BLOB_BASE_FEE,
    Ops.SSTORE: storage_instructions.STACK_SSTORE,
    Ops.TLOAD: storage_instructions.STACK_TLOAD,
    Ops.TSTORE: storage_instructions.STACK_TSTORE,
    Ops.JUMP: control_flow_instructions.STACK_JUMP,
    Ops.JUMPI: control_flow_instructions.STACK_JUMPI,
    Ops.PC: control_flow_instructions.STACK_PC,
    Ops.GAS: control_flow_instructions.STACK_GAS,
    Ops.JUMPDEST: control_flow_instructions.STACK_JUMPDEST,
    Ops.POP: stack_instructions.STACK_POP,
    Ops.PUSH0: stack_instructions.STACK_PUSH0,
    Ops.PUSH1: stack_instructions.STACK_PUSH1,
    Ops.PUSH2: stack_instructions.STACK_PUSH2,
    Ops.PUSH3: stack_instructions.STACK_PUSH3,
    Ops.PUSH4: stack_instructions.STACK_PUSH4,
    Ops.PUSH5: stack_instructions.STACK_PUSH5,
    Ops.PUSH6: stack_instructions.STACK_PUSH6,
    Ops.PUSH7: stack_instructions.STACK_PUSH7,
    Ops.PUSH8: stack_instructions.STACK_PUSH8,
    Ops.PUSH9: stack_instructions.STACK_PUSH9,
    Ops.PUSH10: stack_instructions.STACK_PUSH10,
    Ops.PUSH11: stack_instructions.STACK_PUSH11,
    Ops.PUSH12: stack_instructions.STACK_PUSH12,
    Ops.PUSH13: stack_instructions.STACK_PUSH13,
    Ops.PUSH14: stack_instructions.STACK_PUSH14,
    Ops.PUSH15: stack_instructions.STACK_PUSH15,
    Ops.PUSH16: stack_instructions.STACK_PUSH16,
    Ops.PUSH17: stack_instructions.STACK_PUSH17,
    Ops.PUSH18: stack_instructions.STACK_PUSH18,
    Ops.PUSH19: stack_instructions.STACK_PUSH19,
    Ops.PUSH20: stack_instructions.STACK_PUSH20,
    Ops.PUSH21: stack_instructions.STACK_PUSH21,
    Ops.PUSH22: stack_instructions.STACK_PUSH22,
    Ops.PUSH23: stack_instructions.STACK_PUSH23,
    Ops.PUSH24: stack_instructions.STACK_PUSH24,
    Ops.PUSH25: stack_instructions.STACK_PUSH25,
    Ops.PUSH26: stack_instructions.STACK_PUSH26,
    Ops.PUSH27: stack_instructions.STACK_PUSH27,
    Ops.PUSH28: stack_instructions.STACK_PUSH28,
    Ops.PUSH29: stack_instructions.STACK_PUSH29,
    Ops.PUSH30: stack_instructions.STACK_PUSH30,
    Ops.PUSH31: stack_instructions.STACK_PUSH31,
    Ops.PUSH32: stack_instructions.STACK_PUSH32,
    Ops.DUP1: stack_instructions.STACK_DUP1,
    Ops.DUP2: stack_instructions.STACK_DUP2,
    Ops.DUP3: stack_instructions.STACK_DUP3,
    Ops.DUP4: stack_instructions.STACK_DUP4,
    Ops.DUP5: stack_instructions.STACK_DUP5,
    Ops.DUP6: stack_instructions.STACK_DUP6,
    Ops.DUP7: stack_instructions.STACK_DUP7,
    Ops.DUP8: stack_instructions.STACK_DUP8,
    Ops.DUP9: stack_instructions.STACK_DUP9,
    Ops.DUP10: stack_instructions.STACK_DUP10,
    Ops.DUP11: stack_instructions.STACK_DUP11,
    Ops.DUP12: stack_instructions.STACK_DUP12,
    Ops.DUP13: stack_instructions.STACK_DUP13,
    Ops.DUP14: stack_instructions.STACK_DUP14,
    Ops.DUP15: stack_instructions.STACK_DUP15,
    Ops.DUP16: stack_instructions.STACK_DUP16,
    Ops.SWAP1: stack_instructions.STACK_SWAP1,
    Ops.SWAP2: stack_instructions.STACK_SWAP2,
    Ops.SWAP3: stack_instructions.STACK_SWAP3,
    Ops.SWAP4: stack_instructions.STACK_SWAP4,
    Ops.SWAP5: stack_instructions.STACK_SWAP5,
    Ops.SWAP6: stack_instructions.STACK_SWAP6,
    Ops.SWAP7: stack_instructions.STACK_SWAP7,
    Ops.SWAP8: stack_instructions.STACK_SWAP8,
    Ops.SWAP9: stack_instructions.STACK_SWAP9,
    Ops.SWAP10: stack_instructions.STACK_SWAP10,
    Ops.SWAP11: stack_instructions.STACK_SWAP11,
    Ops.SWAP12: stack_instructions.STACK_SWAP12,
    Ops.SWAP13: stack_instructions.STACK_SWAP13,
    Ops.SWAP14: stack_instructions.STACK_SWAP14,
    Ops.SWAP15: stack_instructions.STACK_SWAP15,
    Ops.SWAP16: stack_instructions.STACK_SWAP16,
    Ops.LOG0: log_instructions.STACK_LOG0,
    Ops.LOG1: log_instructions.STACK_LOG1,
    Ops.LOG2: log_instructions.STACK_LOG2,
    Ops.LOG3: log_instructions.STACK_LOG3,
    Ops.LOG4: log_instructions.STACK_LOG4,
    Ops.DATALOAD: environment_instructions.STACK_DATALOAD,
    Ops.DATALOADN: environment_instructions.STACK_DATALOADN,
    Ops.DATASIZE: environment_instructions.STACK_DATASIZE,
    Ops.DATACOPY: environment_instructions.STACK_DATACOPY,
    Ops.RJUMP: control_flow_instructions.STACK_RJUMP,
    Ops.RJUMPI: control_flow_instructions.STACK_RJUMPI,
    Ops.RJUMPV: control_flow_instructions.STACK_RJUMPV,
    Ops.CALLF: control_flow_instructions.STACK_CALLF,
    Ops.RETF: control_flow_instructions.STACK_RETF,
    Ops.CREATE: system_instructions.STACK_CREATE,
    Ops.RETURN: system_instructions.STACK_RETURN,
    Ops.CALL: system_instructions.STACK_CALL,
    Ops.CALLCODE: system_instructions.STACK_CALLCODE,
    Ops.DELEGATECALL: system_instructions.STACK_DELEGATECALL,
    Ops.SELFDESTRUCT: system_instructions.STACK_SELFDESTRUCT,
    Ops.STATICCALL: system_instructions.STACK_STATICCALL,
    Ops.REVERT: system_instructions.STACK_REVERT,
    Ops.INVALID: system_instructions.STACK_INVALID,
    Ops.CREATE2: system_instructions.STACK_CREATE2,
    Ops.EXTCALL: system_instructions.STACK_EXT_CALL,
    Ops.EXTDELEGATECALL: system_instructions.STACK_EXT_DELEGATECALL,
    Ops.EXTSTATICCALL: system_instructions.STACK_EXT_STATICCALL,
}


EOF1_TERMINATING_INSTRUCTIONS = (
    Ops.RETF,
    Ops.JUMPF,
    Ops.STOP,
    Ops.RETURN,
    Ops.RETURNCONTRACT,
    Ops.REVERT,
    Ops.INVALID,
)
