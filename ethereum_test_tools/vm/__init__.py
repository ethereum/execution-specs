"""
Ethereum Virtual Machine related definitions and utilities.
"""

from .opcode import Macro, Opcode, OpcodeCallArg, Opcodes

__all__ = (
    "Opcode",
    "Macro",
    "OpcodeCallArg",
    "Opcodes",
)
