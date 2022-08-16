"""
Ethereum Virtual Machine (EVM) Gas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""
from ethereum.base_types import U256, Uint
from ethereum.utils.numeric import ceil32

from ..eth_types import Address
from ..state import State, account_exists
from . import Evm
from .exceptions import OutOfGasError

GAS_JUMPDEST = Uint(1)
GAS_BASE = Uint(2)
GAS_VERY_LOW = Uint(3)
GAS_SLOAD = Uint(50)
GAS_STORAGE_SET = Uint(20000)
GAS_STORAGE_UPDATE = Uint(5000)
GAS_STORAGE_CLEAR_REFUND = Uint(15000)
GAS_LOW = Uint(5)
GAS_MID = Uint(8)
GAS_HIGH = Uint(10)
GAS_EXPONENTIATION = Uint(10)
GAS_EXPONENTIATION_PER_BYTE = Uint(10)
GAS_MEMORY = Uint(3)
GAS_KECCAK256 = Uint(30)
GAS_KECCAK256_WORD = Uint(6)
GAS_COPY = Uint(3)
GAS_BLOCK_HASH = Uint(20)
GAS_EXTERNAL = Uint(20)
GAS_BALANCE = Uint(20)
GAS_LOG = Uint(375)
GAS_LOG_DATA = Uint(8)
GAS_LOG_TOPIC = Uint(375)
GAS_CREATE = Uint(32000)
GAS_CODE_DEPOSIT = Uint(200)
GAS_ZERO = Uint(0)
GAS_CALL = Uint(40)
GAS_NEW_ACCOUNT = Uint(25000)
GAS_CALL_VALUE = Uint(9000)
GAS_CALL_STIPEND = Uint(2300)
REFUND_SELF_DESTRUCT = Uint(24000)
GAS_ECRECOVER = Uint(3000)
GAS_SHA256 = Uint(60)
GAS_SHA256_WORD = Uint(12)
GAS_RIPEMD160 = Uint(600)
GAS_RIPEMD160_WORD = Uint(120)
GAS_IDENTITY = Uint(15)
GAS_IDENTITY_WORD = Uint(3)


def charge_gas(evm: Evm, amount: Uint) -> None:
    """
    Subtracts `amount` from `evm.gas_left`.

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of gas the current operation requires.

    Raises
    ------
    :py:class:`~ethereum.homestead.vm.exceptions.OutOfGasError`
        If `gas_left` is less than `amount`.
    """
    if evm.gas_left < amount:
        raise OutOfGasError
    else:
        evm.gas_left -= U256(amount)


def calculate_memory_gas_cost(size_in_bytes: Uint) -> Uint:
    """
    Calculates the gas cost for allocating memory
    to the smallest multiple of 32 bytes,
    such that the allocated size is at least as big as the given size.

    Parameters
    ----------
    size_in_bytes :
        The size of the data in bytes.

    Returns
    -------
    total_gas_cost : `ethereum.base_types.Uint`
        The gas cost for storing data in memory.
    """
    size_in_words = ceil32(size_in_bytes) // 32
    linear_cost = size_in_words * GAS_MEMORY
    quadratic_cost = size_in_words**2 // 512
    total_gas_cost = linear_cost + quadratic_cost
    try:
        return total_gas_cost
    except ValueError:
        raise OutOfGasError


def calculate_gas_extend_memory(
    memory: bytearray, start_position: U256, size: U256
) -> Uint:
    """
    Calculates the gas amount to extend memory

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    start_position :
        Starting pointer to the memory.
    size:
        Amount of bytes by which the memory needs to be extended.

    Returns
    -------
    to_be_paid : `ethereum.base_types.Uint`
        returns `0` if size=0 or if the
        size after extending memory is less than the size before extending
        else it returns the amount that needs to be paid for extendinng memory.
    """
    if size == 0:
        return Uint(0)
    memory_size = Uint(len(memory))
    before_size = ceil32(memory_size)
    after_size = ceil32(Uint(start_position) + Uint(size))
    if after_size <= before_size:
        return Uint(0)
    already_paid = calculate_memory_gas_cost(before_size)
    total_cost = calculate_memory_gas_cost(after_size)
    to_be_paid = total_cost - already_paid
    return to_be_paid


def calculate_call_gas_cost(
    state: State, gas: Uint, to: Address, value: U256
) -> Uint:
    """
    Calculates the gas amount for executing Opcodes `CALL` and `CALLCODE`.

    Parameters
    ----------
    state :
        The current state.
    gas :
        The amount of gas provided to the message-call.
    to:
        The address of the recipient account.
    value:
        The amount of `ETH` that needs to be transferred.

    Returns
    -------
    call_gas_cost: `ethereum.base_types.Uint`
        The total gas amount for executing Opcodes `CALL` and `CALLCODE`.
    """
    _account_exists = account_exists(state, to)
    create_gas_cost = Uint(0) if _account_exists else GAS_NEW_ACCOUNT
    transfer_gas_cost = Uint(0) if value == 0 else GAS_CALL_VALUE
    return GAS_CALL + gas + create_gas_cost + transfer_gas_cost


def calculate_message_call_gas_stipend(value: U256) -> Uint:
    """
    Calculates the gas stipend for making the message call
    with the given value.

    Parameters
    ----------
    value:
        The amount of `ETH` that needs to be transferred.
    Returns
    -------
    message_call_gas_stipend : `ethereum.base_types.Uint`
        The gas stipend for making the message-call.
    """
    return Uint(0) if value == 0 else GAS_CALL_STIPEND
