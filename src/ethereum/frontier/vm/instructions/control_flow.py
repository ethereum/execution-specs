"""
Ethereum Virtual Machine (EVM) Control Flow Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM control flow instructions.
"""
from typing import List

from ethereum.base_types import U256, Uint

from ...vm.error import InvalidJumpDestError
from ...vm.gas import GAS_BASE, GAS_HIGH, GAS_JUMPDEST, GAS_MID
from .. import Evm
from ..operation import Operation, static_gas


def do_stop(evm: Evm, stack: List[U256]) -> None:
    """
    Stop further execution of EVM code.
    """
    evm.running = False


stop = Operation(static_gas(U256(0)), do_stop, 0, 0)


def do_jump(evm: Evm, stack: List[U256], jump_dest: U256) -> None:
    """
    Alter the program counter to the location specified by the top of the
    stack.
    """
    if jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError

    evm.pc = Uint(jump_dest)


jump = Operation(static_gas(GAS_MID), do_jump, 1, 0)


def do_jumpi(
    evm: Evm,
    stack: List[U256],
    conditional_value: U256,
    jump_dest: U256,
) -> None:
    """
    Alter the program counter to the specified location if and only if a
    condition is true. If the condition is not true, then the program counter
    would increase only by 1.
    """
    if conditional_value == 0:
        return

    if jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError

    evm.pc = Uint(jump_dest)


jumpi = Operation(static_gas(GAS_HIGH), do_jumpi, 2, 0)


def do_pc(evm: Evm, stack: List[U256]) -> U256:
    """
    Push onto the stack the value of the program counter after reaching the
    current instruction and without increasing it for the next instruction.
    """
    return U256(evm.pc - 1)


pc = Operation(static_gas(GAS_BASE), do_pc, 0, 1)


def do_gas_left(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the amount of available gas (including the corresponding reduction
    for the cost of this instruction) onto the stack.
    """
    return evm.gas_left


gas_left = Operation(static_gas(GAS_BASE), do_gas_left, 0, 1)


def do_jumpdest(evm: Evm, stack: List[U256]) -> None:
    """
    Mark a valid destination for jumps. This is a noop, present only
    to be used by `JUMP` and `JUMPI` opcodes to verify that their jump is
    valid.
    """
    pass


jumpdest = Operation(static_gas(GAS_JUMPDEST), do_jumpdest, 0, 0)
