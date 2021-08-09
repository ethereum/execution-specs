"""
Ethereum Virtual Machine (EVM) Environmental Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM environment related instructions.
"""

from ethereum.base_types import U256, Uint
from ethereum.frontier.vm.memory import extend_memory, memory_write
from ethereum.utils.address import to_address
from ethereum.utils.numeric import ceil32

from .. import Evm
from ..gas import (
    GAS_BASE,
    GAS_COPY,
    GAS_EXTERNAL,
    GAS_VERY_LOW,
    calculate_gas_extend_memory,
    subtract_gas,
)
from ..stack import pop, push


def address(evm: Evm) -> None:
    """
    Pushes the address of the current executing account to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.current))


def balance(evm: Evm) -> None:
    """
    Pushes the balance of the given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `1`.
    OutOfGasError
        If `evm.gas_left` is less than `20`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.
    evm.gas_left = subtract_gas(evm.gas_left, GAS_EXTERNAL)

    address = to_address(pop(evm.stack))

    account_state = evm.env.state.get(address, None)
    if account_state is None:
        balance = U256(0)
    else:
        balance = U256(account_state.balance)

    push(evm.stack, balance)


def origin(evm: Evm) -> None:
    """
    Pushes the address of the original transaction sender to the stack.
    The origin address can only be an EOA.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.env.origin))


def caller(evm: Evm) -> None:
    """
    Pushes the address of the caller onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.caller))


def callvalue(evm: Evm) -> None:
    """
    Push the value (in wei) sent with the call onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.value)


def calldataload(evm: Evm) -> None:
    """
    Push a word (32 bytes) of the input data belonging to the current
    environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `1`.
    OutOfGasError
        If `evm.gas_left` is less than `3`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    # Converting start_index to Uint from U256 as start_index + 32 can
    # overflow U256.
    start_index = Uint(pop(evm.stack))
    value = evm.data[start_index : start_index + 32]
    # Right pad with 0 so that there are overall 32 bytes.
    value = value.ljust(32, b"\x00")

    push(evm.stack, U256.from_be_bytes(value))


def calldatasize(evm: Evm) -> None:
    """
    Push the size of input data in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(len(evm.data)))


def calldatacopy(evm: Evm) -> None:
    """
    Copy a portion of the input data in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `3`.
    """
    # Converting below to Uint as though the start indices may belong to U256,
    # the ending indices may overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    data_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    gas_cost = (
        GAS_VERY_LOW
        + (GAS_COPY * words)
        + calculate_gas_extend_memory(evm.memory, memory_start_index, size)
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    if size == 0:
        return

    extend_memory(evm.memory, memory_start_index, size)

    value = evm.data[data_start_index : data_start_index + size]
    # But it is possible that data_start_index + size won't exist in evm.data
    # in which case we need to right pad the above obtained bytes with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm.memory, memory_start_index, value)


def codesize(evm: Evm) -> None:
    """
    Push the size of code running in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(len(evm.code)))


def codecopy(evm: Evm) -> None:
    """
    Copy a portion of the code in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `3`.
    """
    # Converting below to Uint as though the start indices may belong to U256,
    # the ending indices may not belong to U256.
    memory_start_index = Uint(pop(evm.stack))
    code_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    gas_cost = (
        GAS_VERY_LOW
        + (GAS_COPY * words)
        + calculate_gas_extend_memory(evm.memory, memory_start_index, size)
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    if size == 0:
        return

    extend_memory(evm.memory, memory_start_index, size)

    value = evm.code[code_start_index : code_start_index + size]
    # But it is possible that code_start_index + size - 1 won't exist in
    # evm.code in which case we need to right pad the above obtained bytes
    # with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm.memory, memory_start_index, value)


def gasprice(evm: Evm) -> None:
    """
    Push the gas price used in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.env.gas_price)


def extcodesize(evm: Evm) -> None:
    """
    Push the code size of a given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `1`.
    OutOfGasError
        If `evm.gas_left` is less than `20`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.
    evm.gas_left = subtract_gas(evm.gas_left, GAS_EXTERNAL)

    address = to_address(pop(evm.stack))

    account_state = evm.env.state.get(address, None)
    if account_state is None:
        codesize = U256(0)
    else:
        codesize = U256(len(evm.env.state[address].code))

    push(evm.stack, codesize)


def extcodecopy(evm: Evm) -> None:
    """
    Copy a portion of an account's code to memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `4`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.

    address = to_address(pop(evm.stack))

    memory_start_index = Uint(pop(evm.stack))
    code_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    gas_cost = (
        GAS_EXTERNAL
        + (GAS_COPY * words)
        + calculate_gas_extend_memory(evm.memory, memory_start_index, size)
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    if size == 0:
        return

    # Get code belonging to another account. In case the other account
    # doesn't exist in the state yet, default to an empty byte code.
    account_state = evm.env.state.get(address, None)
    if account_state is None:
        code = b""
    else:
        code = account_state.code

    extend_memory(evm.memory, memory_start_index, size)

    value = code[code_start_index : code_start_index + size]
    # But it is possible that code_start_index + size won't exist in evm.code
    # in which case we need to right pad the above obtained bytes with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm.memory, memory_start_index, value)
