"""
EOF Valid Opcodes
"""

from typing import List

from ethereum_test_tools.vm.opcode import Opcodes as Op

V1_EOF_OPCODES: List[Op] = [
    # new eof ops
    Op.RJUMP,
    Op.RJUMPI,
    Op.RJUMPV,
    Op.CALLF,
    Op.RETF,
    #  Op.JUMPF,
    Op.STOP,
    Op.ADD,
    Op.MUL,
    Op.SUB,
    Op.DIV,
    Op.SDIV,
    Op.MOD,
    Op.SMOD,
    Op.ADDMOD,
    Op.MULMOD,
    Op.EXP,
    Op.SIGNEXTEND,
    Op.LT,
    Op.GT,
    Op.SLT,
    Op.SGT,
    Op.EQ,
    Op.ISZERO,
    Op.AND,
    Op.OR,
    Op.XOR,
    Op.NOT,
    Op.BYTE,
    Op.SHL,
    Op.SHR,
    Op.SAR,
    Op.SHA3,
    Op.ADDRESS,
    Op.BALANCE,
    Op.ORIGIN,
    Op.CALLER,
    Op.CALLVALUE,
    Op.CALLDATALOAD,
    Op.CALLDATASIZE,
    Op.CALLDATACOPY,
    Op.CODESIZE,
    Op.CODECOPY,
    Op.GASPRICE,
    Op.EXTCODESIZE,
    Op.EXTCODECOPY,
    Op.RETURNDATASIZE,
    Op.RETURNDATACOPY,
    Op.EXTCODEHASH,
    Op.BLOCKHASH,
    Op.COINBASE,
    Op.TIMESTAMP,
    Op.NUMBER,
    Op.PREVRANDAO,
    Op.GASLIMIT,
    Op.CHAINID,
    Op.SELFBALANCE,
    Op.BASEFEE,
    Op.POP,
    Op.MLOAD,
    Op.MSTORE,
    Op.MSTORE8,
    Op.SLOAD,
    Op.SSTORE,
    Op.MSIZE,
    Op.GAS,
    Op.JUMPDEST,
    Op.PUSH1,
    Op.PUSH2,
    Op.PUSH3,
    Op.PUSH4,
    Op.PUSH5,
    Op.PUSH6,
    Op.PUSH7,
    Op.PUSH8,
    Op.PUSH9,
    Op.PUSH10,
    Op.PUSH11,
    Op.PUSH12,
    Op.PUSH13,
    Op.PUSH14,
    Op.PUSH15,
    Op.PUSH16,
    Op.PUSH17,
    Op.PUSH18,
    Op.PUSH19,
    Op.PUSH20,
    Op.PUSH21,
    Op.PUSH22,
    Op.PUSH23,
    Op.PUSH24,
    Op.PUSH25,
    Op.PUSH26,
    Op.PUSH27,
    Op.PUSH28,
    Op.PUSH29,
    Op.PUSH30,
    Op.PUSH31,
    Op.PUSH32,
    Op.DUP1,
    Op.DUP2,
    Op.DUP3,
    Op.DUP4,
    Op.DUP5,
    Op.DUP6,
    Op.DUP7,
    Op.DUP8,
    Op.DUP9,
    Op.DUP10,
    Op.DUP11,
    Op.DUP12,
    Op.DUP13,
    Op.DUP14,
    Op.DUP15,
    Op.DUP16,
    Op.SWAP1,
    Op.SWAP2,
    Op.SWAP3,
    Op.SWAP4,
    Op.SWAP5,
    Op.SWAP6,
    Op.SWAP7,
    Op.SWAP8,
    Op.SWAP9,
    Op.SWAP10,
    Op.SWAP11,
    Op.SWAP12,
    Op.SWAP13,
    Op.SWAP14,
    Op.SWAP15,
    Op.SWAP16,
    Op.LOG0,
    Op.LOG1,
    Op.LOG2,
    Op.LOG3,
    Op.LOG4,
    Op.CREATE,
    Op.CALL,
    # Op.CALLCODE,
    Op.RETURN,
    Op.DELEGATECALL,
    Op.CREATE2,
    Op.STATICCALL,
    Op.REVERT,
    Op.INVALID,
    # Op.SELFDESTRUCT,
]
"""
List of all valid EOF V1 opcodes for Shanghai.
"""

V1_EOF_DEPRECATED_OPCODES = [
    Op.SELFDESTRUCT,
    Op.CALLCODE,
    Op.JUMP,
    Op.JUMPI,
    Op.PC,
]
"""
List of opcodes that will be deprecated for EOF V1.

For these opcodes we will also add the correct expected amount of stack items
so the container is not considered invalid due to buffer underflow.
"""

V1_EOF_ONLY_OPCODES = [
    Op.RJUMP,
    Op.RJUMPI,
    Op.RJUMPV,
    Op.CALLF,
    Op.RETF,
]
"""
List of valid EOF V1 opcodes that are disabled in legacy bytecode.
"""

VALID_TERMINATING_OPCODES = [
    Op.STOP,
    Op.RETURN,
    Op.REVERT,
    Op.INVALID,
    Op.RETF,
]

INVALID_TERMINATING_OPCODES = [op for op in V1_EOF_OPCODES if op not in VALID_TERMINATING_OPCODES]

INVALID_OPCODES = [
    bytes([i])
    for i in range(256)
    if i not in [x.int() for x in V1_EOF_OPCODES] + [x.int() for x in V1_EOF_DEPRECATED_OPCODES]
]
