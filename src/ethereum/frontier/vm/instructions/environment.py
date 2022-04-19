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
from typing import List

from ethereum.base_types import U256, Uint
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...state import get_account
from ...utils.address import to_address
from ...vm.error import OutOfGasError
from ...vm.memory import memory_write, touch_memory
from .. import Evm
from ..gas import (
    GAS_BALANCE,
    GAS_BASE,
    GAS_COPY,
    GAS_EXTERNAL,
    GAS_VERY_LOW,
    subtract_gas,
)
from ..operation import Operation, static_gas


def do_address(evm: Evm, stack: List[U256]) -> U256:
    """
    Pushes the address of the current executing account to the stack.
    """
    return U256.from_be_bytes(evm.message.current_target)


address = Operation(static_gas(GAS_BASE), do_address, 0, 1)


def do_balance(evm: Evm, stack: List[U256], address: U256) -> U256:
    """
    Pushes the balance of the given account onto the stack.
    """
    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    return get_account(evm.env.state, to_address(address)).balance


balance = Operation(static_gas(GAS_BALANCE), do_balance, 1, 1)


def do_origin(evm: Evm, stack: List[U256]) -> U256:
    """
    Pushes the address of the original transaction sender to the stack.
    The origin address can only be an EOA.
    """
    return U256.from_be_bytes(evm.env.origin)


origin = Operation(static_gas(GAS_BASE), do_origin, 0, 1)


def do_caller(evm: Evm, stack: List[U256]) -> U256:
    """
    Pushes the address of the caller onto the stack.
    """
    return U256.from_be_bytes(evm.message.caller)


caller = Operation(static_gas(GAS_BASE), do_caller, 0, 1)


def do_callvalue(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the value (in wei) sent with the call onto the stack.
    """
    return evm.message.value


callvalue = Operation(static_gas(GAS_BASE), do_callvalue, 0, 1)


def do_calldataload(
    evm: Evm, stack: List[U256], start_index_u256: U256
) -> U256:
    """
    Push a word (32 bytes) of the input data belonging to the current
    environment onto the stack.
    """
    # Converting start_index to Uint from U256 as start_index + 32 can
    # overflow U256.
    start_index = Uint(start_index_u256)
    value = evm.message.data[start_index : start_index + 32]
    # Right pad with 0 so that there are overall 32 bytes.
    value = value.ljust(32, b"\x00")

    return U256.from_be_bytes(value)


calldataload = Operation(static_gas(GAS_VERY_LOW), do_calldataload, 1, 1)


def do_calldatasize(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the size of input data in current environment onto the stack.
    """
    return U256(len(evm.message.data))


calldatasize = Operation(static_gas(GAS_BASE), do_calldatasize, 0, 1)


def gas_calldatacopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    data_start_index: U256,
    memory_start_index: U256,
) -> None:
    """
    Copy a portion of the input data in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.
    """
    # Converting below to Uint as though the start indices may belong to U256,
    # the ending indices may overflow U256.
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_VERY_LOW,
        copy_gas_cost,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, total_gas_cost)
    touch_memory(evm, memory_start_index, size)


def do_calldatacopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    data_start_index: U256,
    memory_start_index: U256,
) -> None:
    """
    Copy a portion of the input data in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.
    """
    if size == 0:
        return

    value = evm.message.data[
        data_start_index : Uint(data_start_index) + Uint(size)
    ]
    # But it is possible that data_start_index + size won't exist in evm.data
    # in which case we need to right pad the above obtained bytes with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm, memory_start_index, value)


calldatacopy = Operation(gas_calldatacopy, do_calldatacopy, 3, 0)


def do_codesize(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the size of code running in current environment onto the stack.
    """
    return U256(len(evm.code))


codesize = Operation(static_gas(GAS_BASE), do_codesize, 0, 1)


def gas_codecopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    code_start_index: U256,
    memory_start_index: U256,
) -> None:
    """
    Copy a portion of the code in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.
    """
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_VERY_LOW,
        copy_gas_cost,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, total_gas_cost)
    touch_memory(evm, memory_start_index, size)


def do_codecopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    code_start_index: U256,
    memory_start_index: U256,
) -> None:
    """
    Copy a portion of the code in current environment to memory.

    This will also expand the memory, in case that the memory is insufficient
    to store the data.
    """
    if size == 0:
        return

    value = evm.code[code_start_index : Uint(code_start_index) + Uint(size)]
    # But it is possible that code_start_index + size - 1 won't exist in
    # evm.code in which case we need to right pad the above obtained bytes
    # with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm, memory_start_index, value)


codecopy = Operation(gas_codecopy, do_codecopy, 3, 0)


def do_gasprice(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the gas price used in current environment onto the stack.
    """
    return evm.env.gas_price


gasprice = Operation(static_gas(GAS_BASE), do_gasprice, 0, 1)


def do_extcodesize(evm: Evm, stack: List[U256], address: U256) -> U256:
    """
    Push the code size of a given account onto the stack.
    """
    # Non-existent accounts default to EMPTY_ACCOUNT, which has empty code.
    return U256(len(get_account(evm.env.state, to_address(address)).code))


extcodesize = Operation(static_gas(GAS_EXTERNAL), do_extcodesize, 1, 1)


def gas_extcodecopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    code_start_index: U256,
    memory_start_index: U256,
    address: U256,
) -> None:
    """
    Copy a portion of an account's code to memory.
    """
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = u256_safe_multiply(
        GAS_COPY,
        words,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_EXTERNAL,
        copy_gas_cost,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, total_gas_cost)
    touch_memory(evm, memory_start_index, size)


def do_extcodecopy(
    evm: Evm,
    stack: List[U256],
    size: U256,
    code_start_index: U256,
    memory_start_index: U256,
    address: U256,
) -> None:
    """
    Copy a portion of an account's code to memory.
    """
    if size == 0:
        return

    # Non-existent accounts default to EMPTY_ACCOUNT, which has empty code.
    code = get_account(evm.env.state, to_address(address)).code

    value = code[code_start_index : Uint(code_start_index) + Uint(size)]
    # But it is possible that code_start_index + size won't exist in evm.code
    # in which case we need to right pad the above obtained bytes with 0.
    value = value.ljust(size, b"\x00")

    memory_write(evm, memory_start_index, value)


extcodecopy = Operation(gas_extcodecopy, do_extcodecopy, 4, 0)
