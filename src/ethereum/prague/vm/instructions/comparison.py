"""
Ethereum Virtual Machine (EVM) Comparison Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM Comparison instructions.
"""

from ethereum.base_types import U256

from .. import Evm
from ..gas import GAS_VERY_LOW, charge_gas
from ..stack import pop, push


def less_than(evm: Evm) -> None:
    """
    Checks if the top element is less than the next top element. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = pop(evm.stack)
    right = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(left < right)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1


def signed_less_than(evm: Evm) -> None:
    """
    Signed less-than comparison.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = pop(evm.stack).to_signed()
    right = pop(evm.stack).to_signed()

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(left < right)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1


def greater_than(evm: Evm) -> None:
    """
    Checks if the top element is greater than the next top element. Pushes
    the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = pop(evm.stack)
    right = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(left > right)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1


def signed_greater_than(evm: Evm) -> None:
    """
    Signed greater-than comparison.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = pop(evm.stack).to_signed()
    right = pop(evm.stack).to_signed()

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(left > right)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1


def equal(evm: Evm) -> None:
    """
    Checks if the top element is equal to the next top element. Pushes
    the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = pop(evm.stack)
    right = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(left == right)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1


def is_zero(evm: Evm) -> None:
    """
    Checks if the top element is equal to 0. Pushes the result back on the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    result = U256(x == 0)

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += 1
