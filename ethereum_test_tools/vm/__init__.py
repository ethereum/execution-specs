"""
Ethereum Virtual Machine related definitions and utilities.
"""
from .fork import get_reward, set_fork_requirements
from .opcode import Opcode, Opcodes

__all__ = (
    "Opcode",
    "Opcodes",
    "get_reward",
    "set_fork_requirements",
)
