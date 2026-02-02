"""Ethereum Virtual Machine related definitions and utilities."""

from .bases import (
    ForkOpcodeInterface,
    OpcodeBase,
    OpcodeGasCalculator,
)
from .bytecode import Bytecode, Placeholder
from .helpers import MemoryVariable, call_return_code
from .opcodes import (
    Macro,
    Macros,
    Opcode,
    OpcodeCallArg,
    Opcodes,
)

# Ergonomic alias for the commonly used Opcodes enum
Op = Opcodes

__all__ = (
    "Bytecode",
    "ForkOpcodeInterface",
    "Macro",
    "Macros",
    "MemoryVariable",
    "Op",
    "Opcode",
    "OpcodeBase",
    "OpcodeCallArg",
    "OpcodeGasCalculator",
    "Opcodes",
    "Placeholder",
    "call_return_code",
)
