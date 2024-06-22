"""
Ethereum Virtual Machine related definitions and utilities.
"""

from .bytecode import Bytecode
from .opcode import Macro, Macros, Opcode, OpcodeCallArg, Opcodes, UndefinedOpcodes

__all__ = (
    "Bytecode",
    "Opcode",
    "Macro",
    "Macros",
    "OpcodeCallArg",
    "Opcodes",
    "UndefinedOpcodes",
)
