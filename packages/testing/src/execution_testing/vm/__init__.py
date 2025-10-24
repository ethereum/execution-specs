"""Ethereum Virtual Machine related definitions and utilities."""

from .bytecode import Bytecode
from .evm_types import EVMCodeType
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
    "EVMCodeType",
    "Macro",
    "Macros",
    "MemoryVariable",
    "Op",
    "Opcode",
    "OpcodeCallArg",
    "Opcodes",
    "UndefinedOpcodes",
    "call_return_code",
)
