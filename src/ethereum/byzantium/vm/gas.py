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
from ethereum.utils.safe_arithmetic import u256_safe_add

from . import Evm
from .error import OutOfGasError

GAS_JUMPDEST = U256(1)
GAS_BASE = U256(2)
GAS_VERY_LOW = U256(3)
GAS_SLOAD = U256(200)
GAS_STORAGE_SET = U256(20000)
GAS_STORAGE_UPDATE = U256(5000)
GAS_STORAGE_CLEAR_REFUND = U256(15000)
GAS_LOW = U256(5)
GAS_MID = U256(8)
GAS_HIGH = U256(10)
GAS_EXPONENTIATION = U256(10)
GAS_EXPONENTIATION_PER_BYTE = U256(50)
GAS_MEMORY = U256(3)
GAS_KECCAK256 = U256(30)
GAS_KECCAK256_WORD = U256(6)
GAS_COPY = U256(3)
GAS_BLOCK_HASH = U256(20)
GAS_EXTERNAL = U256(700)
GAS_BALANCE = U256(400)
GAS_LOG = U256(375)
GAS_LOG_DATA = U256(8)
GAS_LOG_TOPIC = U256(375)
GAS_CREATE = U256(32000)
GAS_CODE_DEPOSIT = U256(200)
GAS_ZERO = U256(0)
GAS_CALL = U256(700)
GAS_NEW_ACCOUNT = U256(25000)
GAS_CALL_VALUE = U256(9000)
GAS_CALL_STIPEND = U256(2300)
GAS_SELF_DESTRUCT = U256(5000)
GAS_SELF_DESTRUCT_NEW_ACCOUNT = U256(25000)
REFUND_SELF_DESTRUCT = U256(24000)
GAS_ECRECOVER = U256(3000)
GAS_SHA256 = U256(60)
GAS_SHA256_WORD = U256(12)
GAS_RIPEMD160 = U256(600)
GAS_RIPEMD160_WORD = U256(120)
GAS_IDENTITY = U256(15)
GAS_IDENTITY_WORD = U256(3)
GAS_RETURN_DATA_COPY = U256(3)


def subtract_gas(evm: Evm, amount: U256) -> None:
    """
    Subtracts `amount` from `evm.gas_left`. Raise `OutOfGasError` if that is
    not possible.

    Parameters
    ----------
    evm :
        Current `evm` instance.
    amount :
        The amount of gas to deduct.

    Raises
    ------
    :py:class:`~ethereum.byzantium.vm.error.OutOfGasError`
        If `gas_left` is less than `amount`.
    """
    if evm.gas_left < amount:
        raise OutOfGasError
    else:
        evm.gas_left -= amount


def calculate_memory_gas_cost(size_in_bytes: Uint) -> U256:
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
    total_gas_cost : `ethereum.base_types.U256`
        The gas cost for storing data in memory.
    """
    size_in_words = ceil32(size_in_bytes) // 32
    linear_cost = size_in_words * GAS_MEMORY
    quadratic_cost = size_in_words**2 // 512
    total_gas_cost = linear_cost + quadratic_cost
    try:
        return U256(total_gas_cost)
    except ValueError:
        raise OutOfGasError


def calculate_call_gas_cost(
    gas: U256, gas_left: U256, extra_gas: U256
) -> U256:
    """
    Calculates the gas amount for executing Opcodes `CALL` and `CALLCODE`.

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.
    gas_left :
        The amount of gas left in the current frame.
    extra_gas :
        The amount of gas needed for transferring value + creating a new
        account inside a message call.

    Returns
    -------
    call_gas_cost: `ethereum.base_types.U256`
        The total gas amount for executing Opcodes `CALL` and `CALLCODE`.
    """
    if gas_left < extra_gas:
        raise OutOfGasError

    gas = min(gas, max_message_call_gas(gas_left - extra_gas))

    return u256_safe_add(
        gas,
        extra_gas,
        exception_type=OutOfGasError,
    )


def calculate_message_call_gas_stipend(
    value: U256,
    gas: U256,
    gas_left: U256,
    extra_gas: U256,
    call_stipend: U256 = GAS_CALL_STIPEND,
) -> U256:
    """
    Calculates the gas stipend for making the message call
    with the given value.

    Parameters
    ----------
    value:
        The amount of `ETH` that needs to be transferred.
    gas :
        The amount of gas provided to the message-call.
    gas_left :
        The amount of gas left in the current frame.
    extra_gas :
        The amount of gas needed for transferring value + creating a new
        account inside a message call.
    call_stipend :
        The amount of stipend provided to a message call to execute code while
        transferring value(ETH).

    Returns
    -------
    message_call_gas_stipend : `ethereum.base_types.U256`
        The gas stipend for making the message-call.
    """
    if gas_left < extra_gas:
        raise OutOfGasError

    gas = min(gas, max_message_call_gas(gas_left - extra_gas))
    call_stipend = U256(0) if value == 0 else call_stipend
    return u256_safe_add(
        gas,
        call_stipend,
        exception_type=OutOfGasError,
    )


def max_message_call_gas(gas: U256) -> U256:
    """
    Calculates the maximum gas that is allowed for making a message call

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.

    Returns
    -------
    max_allowed_message_call_gas: `ethereum.base_types.U256`
        The maximum gas allowed for making the message-call.
    """
    return gas - (gas // 64)
