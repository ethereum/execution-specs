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
from ethereum.crypto.hash import keccak256
from ethereum.utils.ensure import ensure
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...eth_types import EMPTY_ACCOUNT
from ...state import get_account
from ...utils.address import to_address
from ...vm.error import OutOfBoundsRead, OutOfGasError
from ...vm.memory import extend_memory, memory_write
from .. import Evm
from ..gas import (
    GAS_BALANCE,
    GAS_BASE,
    GAS_CODE_HASH,
    GAS_COPY,
    GAS_EXTERNAL,
    GAS_FAST_STEP,
    GAS_RETURN_DATA_COPY,
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
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.message.current_target))

    evm.pc += 1


def balance(evm: Evm) -> None:
    """
    Pushes the balance of the given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `20`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BALANCE)

    address = to_address(pop(evm.stack))

    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    balance = get_account(evm.env.state, address).balance

    push(evm.stack, balance)

    evm.pc += 1


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
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.env.origin))

    evm.pc += 1


def caller(evm: Evm) -> None:
    """
    Pushes the address of the caller onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.message.caller))

    evm.pc += 1


def callvalue(evm: Evm) -> None:
    """
    Push the value (in wei) sent with the call onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.message.value)

    evm.pc += 1


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
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `3`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    # Converting start_index to Uint from U256 as start_index + 32 can
    # overflow U256.
    start_index = Uint(pop(evm.stack))
    value = evm.message.data[start_index : start_index + 32]
    # Right pad with 0 so that there are overall 32 bytes.
    value = value.ljust(32, b"\x00")

    push(evm.stack, U256.from_be_bytes(value))

    evm.pc += 1


def calldatasize(evm: Evm) -> None:
    """
    Push the size of input data in current environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(len(evm.message.data)))

    evm.pc += 1


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
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `3`.
    """
    # Converting below to Uint as though the start indices may belong to U256,
    # the ending indices may overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    data_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    memory_extend_gas_cost = calculate_gas_extend_memory(
        evm.memory, memory_start_index, size
    )
    total_gas_cost = u256_safe_add(
        GAS_VERY_LOW,
        copy_gas_cost,
        memory_extend_gas_cost,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)

    evm.pc += 1

    if size == 0:
        return

    extend_memory(evm.memory, memory_start_index, size)

    value = evm.message.data[data_start_index : data_start_index + size]
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
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(len(evm.code)))

    evm.pc += 1


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
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `3`.
    """
    # Converting below to Uint as though the start indices may belong to U256,
    # the ending indices may not belong to U256.
    memory_start_index = Uint(pop(evm.stack))
    code_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    memory_extend_gas_cost = calculate_gas_extend_memory(
        evm.memory, memory_start_index, size
    )
    total_gas_cost = u256_safe_add(
        GAS_VERY_LOW,
        copy_gas_cost,
        memory_extend_gas_cost,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)

    evm.pc += 1

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
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.env.gas_price)

    evm.pc += 1


def extcodesize(evm: Evm) -> None:
    """
    Push the code size of a given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `20`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.
    evm.gas_left = subtract_gas(evm.gas_left, GAS_EXTERNAL)

    address = to_address(pop(evm.stack))

    # Non-existent accounts default to EMPTY_ACCOUNT, which has empty code.
    codesize = U256(len(get_account(evm.env.state, address).code))

    push(evm.stack, codesize)

    evm.pc += 1


def extcodecopy(evm: Evm) -> None:
    """
    Copy a portion of an account's code to memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.StackUnderflowError`
        If `len(stack)` is less than `4`.
    """
    # TODO: There are no test cases against this function. Need to write
    # custom test cases.

    address = to_address(pop(evm.stack))

    memory_start_index = Uint(pop(evm.stack))
    code_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    memory_extend_gas_cost = calculate_gas_extend_memory(
        evm.memory, memory_start_index, size
    )
    total_gas_cost = u256_safe_add(
        GAS_EXTERNAL,
        copy_gas_cost,
        memory_extend_gas_cost,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)

    evm.pc += 1

    if size == 0:
        return

    # Non-existent accounts default to EMPTY_ACCOUNT, which has empty code.
    code = get_account(evm.env.state, address).code

    extend_memory(evm.memory, memory_start_index, size)

    value = code[code_start_index : code_start_index + size]
    # But it is possible that code_start_index + size won't exist in evm.code
    # in which case we need to right pad the above obtained bytes with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm.memory, memory_start_index, value)


def returndatasize(evm: Evm) -> None:
    """
    Pushes the size of the return data buffer onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    return_size = U256(len(evm.return_data))
    push(evm.stack, return_size)
    evm.pc += 1


def returndatacopy(evm: Evm) -> None:
    """
    Copies data from the return data buffer code to memory

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    memory_start_index = Uint(pop(evm.stack))
    return_data_start_position = Uint(pop(evm.stack))
    size = pop(evm.stack)
    ensure(
        return_data_start_position + size <= len(evm.return_data),
        OutOfBoundsRead,
    )

    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_RETURN_DATA_COPY,
        words,
        exception_type=OutOfGasError,
    )
    memory_extend_gas_cost = calculate_gas_extend_memory(
        evm.memory, memory_start_index, size
    )
    total_gas_cost = u256_safe_add(
        GAS_VERY_LOW,
        copy_gas_cost,
        memory_extend_gas_cost,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)

    extend_memory(evm.memory, memory_start_index, size)
    value = evm.return_data[
        return_data_start_position : return_data_start_position + size
    ]
    memory_write(evm.memory, memory_start_index, value)
    evm.pc += 1


def extcodehash(evm: Evm) -> None:
    """
    Returns the keccak256 hash of a contract’s bytecode

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    address = to_address(pop(evm.stack))

    evm.gas_left = subtract_gas(evm.gas_left, GAS_CODE_HASH)

    evm.pc += 1

    account = get_account(evm.env.state, address)

    if account == EMPTY_ACCOUNT:
        push(evm.stack, U256(0))
    else:
        code = account.code
        code_hash = keccak256(code)
        push(evm.stack, U256.from_be_bytes(code_hash))


def self_balance(evm: Evm) -> None:
    """
    Pushes the balance of the current address to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.istanbul.vm.error.OutOfGasError`
        If `evm.gas_left` is less than GAS_FAST_STEP.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_FAST_STEP)

    address = evm.message.current_target

    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    balance = get_account(evm.env.state, address).balance

    push(evm.stack, balance)

    evm.pc += 1
