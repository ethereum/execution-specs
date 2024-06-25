"""
Ethereum Virtual Machine (EVM) Runtime Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Runtime related operations used while executing EVM code.
"""
from typing import Set

from ethereum.base_types import Uint

from . import EOF, get_eof_version
from .instructions import Ops


def get_valid_jump_destinations(container: bytes) -> Set[Uint]:
    """
    Analyze the evm code to obtain the set of valid jump destinations.

    Valid jump destinations are defined as follows:
        * The jump destination is less than the length of the code.
        * The jump destination should have the `JUMPDEST` opcode (0x5B).
        * The jump destination shouldn't be part of the data corresponding to
          `PUSH-N` opcodes.

    Note - Jump destinations are 0-indexed.

    Parameters
    ----------
    container :
        The container for the code. For non-EOF contracts, this is the code.

    Returns
    -------
    valid_jump_destinations: `Set[Uint]`
        The set of valid jump destinations in the code.
    """
    valid_jump_destinations: Set[Uint] = set()
    if get_eof_version(container) != EOF.LEGACY:
        return valid_jump_destinations
    pc = Uint(0)

    while pc < len(container):
        try:
            current_opcode = Ops(container[pc])
        except ValueError:
            # Skip invalid opcodes, as they don't affect the jumpdest
            # analysis. Nevertheless, such invalid opcodes would be caught
            # and raised when the interpreter runs.
            pc += 1
            continue

        if current_opcode == Ops.JUMPDEST:
            valid_jump_destinations.add(pc)
        elif Ops.PUSH1.value <= current_opcode.value <= Ops.PUSH32.value:
            # If PUSH-N opcodes are encountered, skip the current opcode along
            # with the trailing data segment corresponding to the PUSH-N
            # opcodes.
            push_data_size = current_opcode.value - Ops.PUSH1.value + 1
            pc += push_data_size

        pc += 1

    return valid_jump_destinations
