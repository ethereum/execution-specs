"""
Ethereum Virtual Machine (EVM) Runtime Operations.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Runtime related operations used while executing EVM code.
"""

from typing import Set, Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint, ulen

from .instructions import Ops


def get_valid_destinations(code: Bytes) -> Tuple[Set[Uint], Set[Uint]]:
    """
    Analyze the EVM code to obtain the sets of valid jump destinations and
    valid call destinations (EIP-7979), in a single pass.

    Valid jump destinations are defined as follows:
        * The jump destination is less than the length of the code.
        * The jump destination should have the `JUMPDEST` opcode (0x5B) or
          the `CALLDEST` opcode (0xB1, EIP-7979).
        * The jump destination shouldn't be part of the data corresponding to
          `PUSH-N` opcodes.
        * The jump destination shouldn't be part of the immediate byte
          corresponding to `DUPN`, `SWAPN`, or `EXCHANGE` opcodes (EIP-8024).

    Valid call destinations are the `CALLDEST` positions found by the same
    scan: a `CALLDEST` is both a valid call destination and a valid jump
    destination, so that a `JUMP` may enter a subroutine without pushing a
    return address.

    Note - Destinations are 0-indexed.

    Parameters
    ----------
    code :
        The EVM code which is to be executed.

    Returns
    -------
    valid_jump_destinations: `Set[Uint]`
        The set of valid jump destinations in the code.
    valid_call_destinations: `Set[Uint]`
        The set of valid call destinations in the code.

    """
    valid_jump_destinations = set()
    valid_call_destinations = set()
    pc = Uint(0)

    while pc < ulen(code):
        try:
            current_opcode = Ops(code[pc])
        except ValueError:
            # Skip invalid opcodes, as they don't affect the jumpdest
            # analysis. Nevertheless, such invalid opcodes would be caught
            # and raised when the interpreter runs.
            pc += Uint(1)
            continue

        if current_opcode == Ops.JUMPDEST:
            valid_jump_destinations.add(pc)
        elif current_opcode == Ops.CALLDEST:
            valid_call_destinations.add(pc)
            valid_jump_destinations.add(pc)
        elif Ops.PUSH1.value <= current_opcode.value <= Ops.PUSH32.value:
            # If PUSH-N opcodes are encountered, skip the current opcode along
            # with the trailing data segment corresponding to the PUSH-N
            # opcodes.
            push_data_size = current_opcode.value - Ops.PUSH1.value + 1
            pc += Uint(push_data_size)
        elif current_opcode in (Ops.DUPN, Ops.SWAPN):
            # EIP-8024: DUPN/SWAPN invalid immediate range is
            # 90 < x < 128, i.e. 0x5B (91) to 0x7F (127).
            # Invalid immediates are not skipped so the byte
            # remains at an instruction boundary.
            if (
                pc + Uint(1) < ulen(code)
                and 0x5B <= code[pc + Uint(1)] <= 0x7F
            ):
                pass
            else:
                pc += Uint(1)
        elif current_opcode == Ops.EXCHANGE:
            # EIP-8024: EXCHANGE invalid immediate range is
            # 81 < x < 128, i.e. 0x52 (82) to 0x7F (127).
            # Invalid immediates are not skipped so the byte
            # remains at an instruction boundary.
            if (
                pc + Uint(1) < ulen(code)
                and 0x52 <= code[pc + Uint(1)] <= 0x7F
            ):
                pass
            else:
                pc += Uint(1)

        pc += Uint(1)

    return valid_jump_destinations, valid_call_destinations
