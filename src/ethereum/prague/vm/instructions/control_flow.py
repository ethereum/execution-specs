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

from ...vm.gas import (
    GAS_BASE,
    GAS_CALLF,
    GAS_HIGH,
    GAS_JUMPDEST,
    GAS_MID,
    GAS_RETF,
    GAS_RJUMP,
    GAS_RJUMPI,
    GAS_RJUMPV,
    charge_gas,
)
from .. import Evm, OpcodeStackItemCount, ReturnStackItem
from ..exceptions import ExceptionalHalt, InvalidJumpDestError
from ..stack import pop, push

STACK_STOP = OpcodeStackItemCount(inputs=0, outputs=0)
STACK_JUMP = OpcodeStackItemCount(inputs=1, outputs=0)
STACK_JUMPI = OpcodeStackItemCount(inputs=2, outputs=0)
STACK_PC = OpcodeStackItemCount(inputs=0, outputs=1)
STACK_GAS = OpcodeStackItemCount(inputs=0, outputs=1)
STACK_JUMPDEST = OpcodeStackItemCount(inputs=0, outputs=0)
STACK_RJUMP = OpcodeStackItemCount(inputs=0, outputs=0)
STACK_RJUMPI = OpcodeStackItemCount(inputs=1, outputs=0)
STACK_RJUMPV = OpcodeStackItemCount(inputs=1, outputs=0)
STACK_CALLF = OpcodeStackItemCount(inputs=0, outputs=0)
STACK_RETF = OpcodeStackItemCount(inputs=0, outputs=0)


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
    evm.pc += 1


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
    charge_gas(evm, GAS_MID)

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
    charge_gas(evm, GAS_HIGH)

    # OPERATION
    if conditional_value == 0:
        destination = evm.pc + 1
    elif jump_dest not in evm.valid_jump_destinations:
        raise InvalidJumpDestError
    else:
        destination = jump_dest

    # PROGRAM COUNTER
    evm.pc = Uint(destination)


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
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(evm.pc))

    # PROGRAM COUNTER
    evm.pc += 1


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
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(evm.gas_left))

    # PROGRAM COUNTER
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

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_JUMPDEST)

    # OPERATION
    pass

    # PROGRAM COUNTER
    evm.pc += 1


def rjump(evm: Evm) -> None:
    """
    Jump to a relative offset.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_RJUMP)

    # OPERATION
    pass

    # PROGRAM COUNTER
    relative_offset = int.from_bytes(
        evm.code[evm.pc + 1 : evm.pc + 3], "big", signed=True
    )
    # pc + 1 + 2 bytes of relative offset
    pc_post_instruction = int(evm.pc) + 3
    evm.pc = Uint(pc_post_instruction + relative_offset)


def rjumpi(evm: Evm) -> None:
    """
    Jump to a relative offset given a condition.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    condition = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_RJUMPI)

    # OPERATION
    pass

    # PROGRAM COUNTER
    relative_offset = int.from_bytes(
        evm.code[evm.pc + 1 : evm.pc + 3], "big", signed=True
    )
    # pc + 1 + 2 bytes of relative offset
    pc_post_instruction = int(evm.pc) + 3
    if condition == 0:
        evm.pc = Uint(pc_post_instruction)
    else:
        evm.pc = Uint(pc_post_instruction + relative_offset)


def rjumpv(evm: Evm) -> None:
    """
    Jump to a relative offset via jump table.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    case = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_RJUMPV)

    # OPERATION
    pass

    # PROGRAM COUNTER
    max_index = evm.code[evm.pc + 1]
    num_relative_indices = max_index + 1
    # pc_post_instruction will be
    # counter + 1 <- for normal pc increment to next opcode
    # + 1 <- for the 1 byte max_index
    # + 2 * num_relative_indices <- for the 2 bytes of each offset
    pc_post_instruction = int(evm.pc) + 2 + 2 * num_relative_indices

    if case > max_index:
        evm.pc = Uint(pc_post_instruction)
    else:
        relative_offset_position = evm.pc + 2 + 2 * case
        relative_offset = int.from_bytes(
            evm.code[relative_offset_position : relative_offset_position + 2],
            "big",
            signed=True,
        )
        evm.pc = Uint(pc_post_instruction + relative_offset)


def callf(evm: Evm) -> None:
    """
    Call a function in EOF

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_CALLF)

    # OPERATION
    assert evm.eof_metadata is not None
    target_section_index = Uint.from_be_bytes(
        evm.code[evm.pc + 1 : evm.pc + 3]
    )
    target_section = evm.eof_metadata.type_section_contents[
        target_section_index
    ]
    target_inputs = Uint(target_section[0])
    target_max_stack_height = Uint.from_be_bytes(target_section[2:])

    if len(evm.stack) > 1024 - target_max_stack_height + target_inputs:
        raise ExceptionalHalt
    if len(evm.return_stack) == 1024:
        raise ExceptionalHalt

    evm.return_stack.append(
        ReturnStackItem(
            code_section_index=evm.current_section_index,
            offset=evm.pc + 3,
        )
    )

    # PROGRAM COUNTER
    evm.current_section_index = target_section_index
    evm.code = evm.eof_metadata.code_section_contents[target_section_index]
    evm.pc = Uint(0)


def retf(evm: Evm) -> None:
    """
    Return from a function in EOF

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_RETF)

    # OPERATION
    pass

    # PROGRAM COUNTER
    assert evm.eof_metadata is not None
    return_stack_item = evm.return_stack.pop()
    evm.current_section_index = return_stack_item.code_section_index
    evm.code = evm.eof_metadata.code_section_contents[
        evm.current_section_index
    ]
    evm.pc = return_stack_item.offset
