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

from ethereum.base_types import U256, Uint

from ...vm.gas import GAS_BASE, GAS_HIGH, GAS_JUMPDEST, GAS_MID, subtract_gas
from .. import Evm
from ..exceptions import InvalidJumpDestError
from ..stack import pop, push


def stop(evm: Evm) -> None:
    """
    Stop further execution of EVM code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.running = False


def jump(evm: Evm) -> None:
    """
    Alter the program counter to the location specified by the top of the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.InvalidJumpDestError`
        If the jump destination doesn't meet any of the following criteria:
            * The jump destination is less than the length of the code.
            * The jump destination should have the `JUMPDEST` opcode (0x5B).
            * The jump destination shouldn't be part of the data corresponding
            to `PUSH-N` opcodes.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `8`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_MID)
    jump_dest = pop(evm.stack)

    if jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError

    evm.pc = Uint(jump_dest)


def jumpi(evm: Evm) -> None:
    """
    Alter the program counter to the specified location if and only if a
    condition is true. If the condition is not true, then the program counter
    would increase only by 1.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.InvalidJumpDestError`
        If the jump destination doesn't meet any of the following criteria:
            * The jump destination is less than the length of the code.
            * The jump destination should have the `JUMPDEST` opcode (0x5B).
            * The jump destination shouldn't be part of the data corresponding
            to `PUSH-N` opcodes.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `10`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_HIGH)

    jump_dest = pop(evm.stack)
    conditional_value = pop(evm.stack)

    if conditional_value == 0:
        evm.pc += 1
        return

    if jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError

    evm.pc = Uint(jump_dest)


def pc(evm: Evm) -> None:
    """
    Push onto the stack the value of the program counter after reaching the
    current instruction and without increasing it for the next instruction.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.StackOverflowError`
        If `len(stack)` is more than `1023`.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(evm.pc))
    evm.pc += 1


def gas_left(evm: Evm) -> None:
    """
    Push the amount of available gas (including the corresponding reduction
    for the cost of this instruction) onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.StackOverflowError`
        If `len(stack)` is more than `1023`.
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.gas_left)
    evm.pc += 1


def jumpdest(evm: Evm) -> None:
    """
    Mark a valid destination for jumps. This is a noop, present only
    to be used by `JUMP` and `JUMPI` opcodes to verify that their jump is
    valid.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.spurious_dragon.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `1`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_JUMPDEST)
    evm.pc += 1
