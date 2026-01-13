"""Ethereum Virtual Machine related definitions and utilities."""

from .bases import (
    ForkOpcodeInterface,
    OpcodeBase,
    OpcodeGasCalculator,
)
from .bytecode import Bytecode
from .helpers import MemoryVariable, call_return_code
from .opcodes import (
    Macro,
    Macros,
    Opcode,
    OpcodeCallArg,
    Opcodes,
    UndefinedOpcodes,
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
    "UndefinedOpcodes",
    "call_return_code",
)
