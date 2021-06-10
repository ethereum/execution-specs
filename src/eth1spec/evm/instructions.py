"""
EVM Instructions
----------------------
"""


from ..eth_types import U256, Uint
from . import Evm
from .gas import GAS_VERY_LOW, subtract_gas
from .stack import pop, push


def add(evm: Evm) -> None:
    """
    Adds the top two elements of the stack together, and pushes the result back
    on the stack.

    Parameters
    ----------
    evm : `Evm`
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)

    val = x + y

    push(evm.stack, val)


def sstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's storage.

    Parameters
    ----------
    evm : `Evm`
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `20000`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, Uint(20000))

    k = pop(evm.stack)
    v = pop(evm.stack)

    evm.env.state[evm.current].storage[k.to_be_bytes32()] = v


def push1(evm: Evm) -> None:
    """
    Pushes a one-byte immediate onto the stack.

    Parameters
    ----------
    evm : `Evm`
        The current EVM frame.

    Raises
    ------
    StackOverflowError
        If `len(stack)` is equals `1024`.
    OutOfGasError
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    push(evm.stack, U256(evm.code[evm.pc + 1]))
    evm.pc += 1
