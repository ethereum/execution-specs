"""
Ethereum Virtual Machine (EVM) Control Flow Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM control flow instructions.
"""

from ethereum_types.numeric import U256, Uint

from ...vm.gas import (
    GasCosts,
    charge_gas,
)
from .. import RETURN_STACK_LIMIT, Evm
from ..exceptions import (
    InvalidJumpDestError,
    ReturnStackOverflowError,
    ReturnStackUnderflowError,
)
from ..stack import pop, push


def stop(evm: Evm) -> None:
    """
    Stop further execution of EVM code.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    pass

    # OPERATION
    evm.running = False

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def jump(evm: Evm) -> None:
    """
    Alter the program counter to the location specified by the top of the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    jump_dest = Uint(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_JUMP)

    # OPERATION
    if jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError

    # PROGRAM COUNTER
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

    """
    # STACK
    jump_dest = Uint(pop(evm.stack))
    conditional_value = pop(evm.stack)

    # GAS
    charge_gas(evm, GasCosts.OPCODE_JUMPI)

    # OPERATION
    if conditional_value == 0:
        destination = evm.pc + Uint(1)
    elif jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError
    else:
        destination = jump_dest

    # PROGRAM COUNTER
    evm.pc = destination


def pc(evm: Evm) -> None:
    """
    Push onto the stack the value of the program counter after reaching the
    current instruction and without increasing it for the next instruction.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_PC)

    # OPERATION
    push(evm.stack, U256(evm.pc))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def gas_left(evm: Evm) -> None:
    """
    Push the amount of available gas (including the corresponding reduction
    for the cost of this instruction) onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_GAS)

    # OPERATION
    push(evm.stack, U256(evm.gas_meter.gas_left))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def jumpdest(evm: Evm) -> None:
    """
    Mark a valid destination for jumps. This is a noop, present only
    to be used by `JUMP` and `JUMPI` opcodes to verify that their jump is
    valid.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_JUMPDEST)

    # OPERATION
    pass

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def callsub(evm: Evm) -> None:
    """
    Transfer control to a subroutine (EIP-7979): push the position of the
    next instruction onto the return stack and jump to the `CALLDEST` whose
    position is on top of the data stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    destination = Uint(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLSUB)

    # OPERATION
    if destination not in evm.valid_call_destinations:
        raise InvalidJumpDestError
    if Uint(len(evm.return_stack)) >= RETURN_STACK_LIMIT:
        raise ReturnStackOverflowError
    evm.return_stack.append(evm.pc + Uint(1))

    # PROGRAM COUNTER
    evm.pc = destination


def calldest(evm: Evm) -> None:
    """
    Mark a subroutine entry (EIP-7979). Like `JUMPDEST`, this is a noop:
    it is the only valid destination of a `CALLSUB`, and also a valid
    destination of `JUMP` and `JUMPI`, which enter the subroutine without
    pushing a return address.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLDEST)

    # OPERATION
    pass

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def returnsub(evm: Evm) -> None:
    """
    Return control to the most recent caller (EIP-7979): pop the return
    stack into the program counter.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_RETURNSUB)

    # OPERATION
    if len(evm.return_stack) == 0:
        raise ReturnStackUnderflowError

    # PROGRAM COUNTER
    evm.pc = evm.return_stack.pop()
