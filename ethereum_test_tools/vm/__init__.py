"""
Ethereum Virtual Machine related definitions and utilities.
"""

from .opcode import Macro, Macros, Opcode, OpcodeCallArg, Opcodes

__all__ = (
    "Opcode",
    "Macro",
    "Macros",
    "OpcodeCallArg",
    "Opcodes",
)
