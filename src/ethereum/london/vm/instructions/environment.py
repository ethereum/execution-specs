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

from ...fork_types import EMPTY_ACCOUNT
from ...state import get_account
from ...utils.address import to_address
from ...vm.memory import buffer_read, memory_write
from .. import Evm
from ..exceptions import OutOfBoundsRead
from ..gas import (
    GAS_BASE,
    GAS_COLD_ACCOUNT_ACCESS,
    GAS_COPY,
    GAS_FAST_STEP,
    GAS_RETURN_DATA_COPY,
    GAS_VERY_LOW,
    GAS_WARM_ACCESS,
    calculate_gas_extend_memory,
    charge_gas,
)
from ..stack import pop, push


def address(evm: Evm) -> None:
    """
    Pushes the address of the current executing account to the stack.

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
    push(evm.stack, U256.from_be_bytes(evm.message.current_target))

    # PROGRAM COUNTER
    evm.pc += 1


def balance(evm: Evm) -> None:
    """
    Pushes the balance of the given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        charge_gas(evm, GAS_WARM_ACCESS)
    else:
        evm.accessed_addresses.add(address)
        charge_gas(evm, GAS_COLD_ACCOUNT_ACCESS)

    # OPERATION
    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    balance = get_account(evm.env.state, address).balance

    push(evm.stack, balance)

    # PROGRAM COUNTER
    evm.pc += 1


def origin(evm: Evm) -> None:
    """
    Pushes the address of the original transaction sender to the stack.
    The origin address can only be an EOA.

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
    push(evm.stack, U256.from_be_bytes(evm.env.origin))

    # PROGRAM COUNTER
    evm.pc += 1


def caller(evm: Evm) -> None:
    """
    Pushes the address of the caller onto the stack.

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
    push(evm.stack, U256.from_be_bytes(evm.message.caller))

    # PROGRAM COUNTER
    evm.pc += 1


def callvalue(evm: Evm) -> None:
    """
    Push the value (in wei) sent with the call onto the stack.

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
    push(evm.stack, evm.message.value)

    # PROGRAM COUNTER
    evm.pc += 1


def calldataload(evm: Evm) -> None:
    """
    Push a word (32 bytes) of the input data belonging to the current
    environment onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_index = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    value = buffer_read(evm.message.data, start_index, U256(32))

    push(evm.stack, U256.from_be_bytes(value))

    # PROGRAM COUNTER
    evm.pc += 1


def calldatasize(evm: Evm) -> None:
    """
    Push the size of input data in current environment onto the stack.

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
    push(evm.stack, U256(len(evm.message.data)))

    # PROGRAM COUNTER
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

    """
    # STACK
    memory_start_index = pop(evm.stack)
    data_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = GAS_COPY * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(evm, GAS_VERY_LOW + copy_gas_cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(evm.message.data, data_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += 1


def codesize(evm: Evm) -> None:
    """
    Push the size of code running in current environment onto the stack.

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
    push(evm.stack, U256(len(evm.code)))

    # PROGRAM COUNTER
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

    """
    # STACK
    memory_start_index = pop(evm.stack)
    code_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = GAS_COPY * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(evm, GAS_VERY_LOW + copy_gas_cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = buffer_read(evm.code, code_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += 1


def gasprice(evm: Evm) -> None:
    """
    Push the gas price used in current environment onto the stack.

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
    push(evm.stack, U256(evm.env.gas_price))

    # PROGRAM COUNTER
    evm.pc += 1


def extcodesize(evm: Evm) -> None:
    """
    Push the code size of a given account onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        charge_gas(evm, GAS_WARM_ACCESS)
    else:
        evm.accessed_addresses.add(address)
        charge_gas(evm, GAS_COLD_ACCOUNT_ACCESS)

    # OPERATION
    # Non-existent accounts default to EMPTY_ACCOUNT, which has empty code.
    codesize = U256(len(get_account(evm.env.state, address).code))

    push(evm.stack, codesize)

    # PROGRAM COUNTER
    evm.pc += 1


def extcodecopy(evm: Evm) -> None:
    """
    Copy a portion of an account's code to memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    address = to_address(pop(evm.stack))
    memory_start_index = pop(evm.stack)
    code_start_index = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = GAS_COPY * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )

    if address in evm.accessed_addresses:
        charge_gas(evm, GAS_WARM_ACCESS + copy_gas_cost + extend_memory.cost)
    else:
        evm.accessed_addresses.add(address)
        charge_gas(
            evm, GAS_COLD_ACCOUNT_ACCESS + copy_gas_cost + extend_memory.cost
        )

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    code = get_account(evm.env.state, address).code
    value = buffer_read(code, code_start_index, size)
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += 1


def returndatasize(evm: Evm) -> None:
    """
    Pushes the size of the return data buffer onto the stack.

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
    push(evm.stack, U256(len(evm.return_data)))

    # PROGRAM COUNTER
    evm.pc += 1


def returndatacopy(evm: Evm) -> None:
    """
    Copies data from the return data buffer code to memory

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    memory_start_index = pop(evm.stack)
    return_data_start_position = pop(evm.stack)
    size = pop(evm.stack)

    # GAS
    words = ceil32(Uint(size)) // 32
    copy_gas_cost = GAS_RETURN_DATA_COPY * words
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(memory_start_index, size)]
    )
    charge_gas(evm, GAS_VERY_LOW + copy_gas_cost + extend_memory.cost)

    # OPERATION
    ensure(
        Uint(return_data_start_position) + Uint(size) <= len(evm.return_data),
        OutOfBoundsRead,
    )

    evm.memory += b"\x00" * extend_memory.expand_by
    value = evm.return_data[
        return_data_start_position : return_data_start_position + size
    ]
    memory_write(evm.memory, memory_start_index, value)

    # PROGRAM COUNTER
    evm.pc += 1


def extcodehash(evm: Evm) -> None:
    """
    Returns the keccak256 hash of a contract’s bytecode
    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    # STACK
    address = to_address(pop(evm.stack))

    # GAS
    if address in evm.accessed_addresses:
        charge_gas(evm, GAS_WARM_ACCESS)
    else:
        evm.accessed_addresses.add(address)
        charge_gas(evm, GAS_COLD_ACCOUNT_ACCESS)

    # OPERATION
    account = get_account(evm.env.state, address)

    if account == EMPTY_ACCOUNT:
        codehash = U256(0)
    else:
        codehash = U256.from_be_bytes(keccak256(account.code))

    push(evm.stack, codehash)

    # PROGRAM COUNTER
    evm.pc += 1


def self_balance(evm: Evm) -> None:
    """
    Pushes the balance of the current address to the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_FAST_STEP)

    # OPERATION
    # Non-existent accounts default to EMPTY_ACCOUNT, which has balance 0.
    balance = get_account(evm.env.state, evm.message.current_target).balance

    push(evm.stack, balance)

    # PROGRAM COUNTER
    evm.pc += 1


def base_fee(evm: Evm) -> None:
    """
    Pushes the base fee of the current block on to the stack.

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
    push(evm.stack, U256(evm.env.base_fee_per_gas))

    # PROGRAM COUNTER
    evm.pc += 1
