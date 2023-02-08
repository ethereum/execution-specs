"""
Ethereum Virtual Machine (EVM) Stack Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM stack related instructions.
"""

from functools import partial

from ethereum.base_types import U256
from ethereum.utils.ensure import ensure

from .. import Evm, stack
from ..exceptions import StackUnderflowError
from ..gas import GAS_BASE, GAS_VERY_LOW, charge_gas
from ..memory import buffer_read


def pop(evm: Evm) -> None:
    """
    Remove item from stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    stack.pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    pass

    # PROGRAM COUNTER
    evm.pc += 1


def push_n(evm: Evm, num_bytes: int) -> None:
    """
    Pushes a N-byte immediate onto the stack. Push zero if num_bytes is zero.

    Parameters
    ----------
    evm :
        The current EVM frame.

    num_bytes :
        The number of immediate bytes to be read from the code and pushed to
        the stack. Push zero if num_bytes is zero.

    """
    # STACK
    pass

    # GAS
    if num_bytes == 0:
        charge_gas(evm, GAS_BASE)
    else:
        charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    data_to_push = U256.from_be_bytes(
        buffer_read(evm.code, U256(evm.pc + 1), U256(num_bytes))
    )
    stack.push(evm.stack, data_to_push)

    # PROGRAM COUNTER
    evm.pc += 1 + num_bytes


def dup_n(evm: Evm, item_number: int) -> None:
    """
    Duplicate the Nth stack item (from top of the stack) to the top of stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    item_number :
        The stack item number (0-indexed from top of stack) to be duplicated
        to the top of stack.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    ensure(item_number < len(evm.stack), StackUnderflowError)
    data_to_duplicate = evm.stack[len(evm.stack) - 1 - item_number]
    stack.push(evm.stack, data_to_duplicate)

    # PROGRAM COUNTER
    evm.pc += 1


def swap_n(evm: Evm, item_number: int) -> None:
    """
    Swap the top and the `item_number` element of the stack, where
    the top of the stack is position zero.

    If `item_number` is zero, this function does nothing (which should not be
    possible, since there is no `SWAP0` instruction).

    Parameters
    ----------
    evm :
        The current EVM frame.

    item_number :
        The stack item number (0-indexed from top of stack) to be swapped
        with the top of stack element.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    ensure(item_number < len(evm.stack), StackUnderflowError)
    evm.stack[-1], evm.stack[-1 - item_number] = (
        evm.stack[-1 - item_number],
        evm.stack[-1],
    )

    # PROGRAM COUNTER
    evm.pc += 1


push0 = partial(push_n, num_bytes=0)
push1 = partial(push_n, num_bytes=1)
push2 = partial(push_n, num_bytes=2)
push3 = partial(push_n, num_bytes=3)
push4 = partial(push_n, num_bytes=4)
push5 = partial(push_n, num_bytes=5)
push6 = partial(push_n, num_bytes=6)
push7 = partial(push_n, num_bytes=7)
push8 = partial(push_n, num_bytes=8)
push9 = partial(push_n, num_bytes=9)
push10 = partial(push_n, num_bytes=10)
push11 = partial(push_n, num_bytes=11)
push12 = partial(push_n, num_bytes=12)
push13 = partial(push_n, num_bytes=13)
push14 = partial(push_n, num_bytes=14)
push15 = partial(push_n, num_bytes=15)
push16 = partial(push_n, num_bytes=16)
push17 = partial(push_n, num_bytes=17)
push18 = partial(push_n, num_bytes=18)
push19 = partial(push_n, num_bytes=19)
push20 = partial(push_n, num_bytes=20)
push21 = partial(push_n, num_bytes=21)
push22 = partial(push_n, num_bytes=22)
push23 = partial(push_n, num_bytes=23)
push24 = partial(push_n, num_bytes=24)
push25 = partial(push_n, num_bytes=25)
push26 = partial(push_n, num_bytes=26)
push27 = partial(push_n, num_bytes=27)
push28 = partial(push_n, num_bytes=28)
push29 = partial(push_n, num_bytes=29)
push30 = partial(push_n, num_bytes=30)
push31 = partial(push_n, num_bytes=31)
push32 = partial(push_n, num_bytes=32)

dup1 = partial(dup_n, item_number=0)
dup2 = partial(dup_n, item_number=1)
dup3 = partial(dup_n, item_number=2)
dup4 = partial(dup_n, item_number=3)
dup5 = partial(dup_n, item_number=4)
dup6 = partial(dup_n, item_number=5)
dup7 = partial(dup_n, item_number=6)
dup8 = partial(dup_n, item_number=7)
dup9 = partial(dup_n, item_number=8)
dup10 = partial(dup_n, item_number=9)
dup11 = partial(dup_n, item_number=10)
dup12 = partial(dup_n, item_number=11)
dup13 = partial(dup_n, item_number=12)
dup14 = partial(dup_n, item_number=13)
dup15 = partial(dup_n, item_number=14)
dup16 = partial(dup_n, item_number=15)

swap1 = partial(swap_n, item_number=1)
swap2 = partial(swap_n, item_number=2)
swap3 = partial(swap_n, item_number=3)
swap4 = partial(swap_n, item_number=4)
swap5 = partial(swap_n, item_number=5)
swap6 = partial(swap_n, item_number=6)
swap7 = partial(swap_n, item_number=7)
swap8 = partial(swap_n, item_number=8)
swap9 = partial(swap_n, item_number=9)
swap10 = partial(swap_n, item_number=10)
swap11 = partial(swap_n, item_number=11)
swap12 = partial(swap_n, item_number=12)
swap13 = partial(swap_n, item_number=13)
swap14 = partial(swap_n, item_number=14)
swap15 = partial(swap_n, item_number=15)
swap16 = partial(swap_n, item_number=16)
