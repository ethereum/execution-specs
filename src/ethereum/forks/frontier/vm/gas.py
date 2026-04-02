"""
Ethereum Virtual Machine (EVM) Gas.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""

from dataclasses import dataclass
from typing import List, Tuple

from ethereum_types.numeric import U256, Uint

from ethereum.state import Address
from ethereum.trace import GasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32

from ..state import State, account_exists
from . import Evm
from .exceptions import OutOfGasError


class GasCosts:
    """
    Constant gas values for the EVM.

    These values may be patched at runtime by a future gas repricing utility
    """

    # Tiers
    BASE = Uint(2)
    VERY_LOW = Uint(3)
    LOW = Uint(5)
    MID = Uint(8)
    HIGH = Uint(10)

    # Access Costs
    SLOAD = Uint(50)

    # Storage Costs
    STORAGE_SET = Uint(20000)
    COLD_STORAGE_WRITE = Uint(5000)

    # Call Costs
    CALL_VALUE = Uint(9000)
    CALL_STIPEND = Uint(2300)
    NEW_ACCOUNT = Uint(25000)

    # Contract Creation Costs
    CODE_DEPOSIT_PER_BYTE = Uint(200)

    # Utility
    ZERO = Uint(0)

    # Refunds
    REFUND_STORAGE_CLEAR = 15000
    REFUND_SELF_DESTRUCT = Uint(24000)

    # Precompiles
    PRECOMPILE_ECRECOVER = Uint(3000)
    PRECOMPILE_SHA256_BASE = Uint(60)
    PRECOMPILE_SHA256_PER_WORD = Uint(12)
    PRECOMPILE_RIPEMD160_BASE = Uint(600)
    PRECOMPILE_RIPEMD160_PER_WORD = Uint(120)
    PRECOMPILE_IDENTITY_BASE = Uint(15)
    PRECOMPILE_IDENTITY_PER_WORD = Uint(3)

    # Opcodes
    OPCODE_ADD = VERY_LOW
    OPCODE_SUB = VERY_LOW
    OPCODE_MUL = LOW
    OPCODE_DIV = LOW
    OPCODE_SDIV = LOW
    OPCODE_MOD = LOW
    OPCODE_SMOD = LOW
    OPCODE_ADDMOD = MID
    OPCODE_MULMOD = MID
    OPCODE_SIGNEXTEND = LOW
    OPCODE_LT = VERY_LOW
    OPCODE_GT = VERY_LOW
    OPCODE_SLT = VERY_LOW
    OPCODE_SGT = VERY_LOW
    OPCODE_EQ = VERY_LOW
    OPCODE_ISZERO = VERY_LOW
    OPCODE_AND = VERY_LOW
    OPCODE_OR = VERY_LOW
    OPCODE_XOR = VERY_LOW
    OPCODE_NOT = VERY_LOW
    OPCODE_BYTE = VERY_LOW
    OPCODE_JUMP = MID
    OPCODE_JUMPI = HIGH
    OPCODE_JUMPDEST = Uint(1)
    OPCODE_CALLDATALOAD = VERY_LOW
    OPCODE_BLOCKHASH = Uint(20)
    OPCODE_COINBASE = BASE
    OPCODE_PUSH = VERY_LOW
    OPCODE_DUP = VERY_LOW
    OPCODE_SWAP = VERY_LOW

    # Dynamic Opcodes
    COPY_PER_WORD = Uint(3)
    OPCODE_CALLDATACOPY = VERY_LOW
    OPCODE_CODECOPY = VERY_LOW
    OPCODE_MLOAD = VERY_LOW
    OPCODE_MSTORE = VERY_LOW
    OPCODE_MSTORE8 = VERY_LOW

    # TODO
    MEMORY = Uint(3)
    EXTERNAL = Uint(20)
    BALANCE = Uint(20)
    CREATE = Uint(32000)
    CALL = Uint(40)
    EXPONENTIATION = Uint(10)
    EXPONENTIATION_PER_BYTE = Uint(10)
    KECCAK256 = Uint(30)
    KECCAK256_PER_WORD = Uint(6)
    LOG = Uint(375)
    LOG_DATA_PER_BYTE = Uint(8)
    LOG_TOPIC = Uint(375)


@dataclass
class ExtendMemory:
    """
    Define the parameters for memory extension in opcodes.

    `cost`: `ethereum.base_types.Uint`
        The gas required to perform the extension
    `expand_by`: `ethereum.base_types.Uint`
        The size by which the memory will be extended
    """

    cost: Uint
    expand_by: Uint


@dataclass
class MessageCallGas:
    """
    Define the gas cost and gas given to the sub-call for executing the call
    opcodes.

    `cost`: `ethereum.base_types.Uint`
        The gas required to execute the call opcode, excludes
        memory expansion costs.
    `sub_call`: `ethereum.base_types.Uint`
        The portion of gas available to sub-calls that is refundable
        if not consumed.
    """

    cost: Uint
    sub_call: Uint


def charge_gas(evm: Evm, amount: Uint) -> None:
    """
    Subtracts `amount` from `evm.gas_left`.

    Parameters
    ----------
    evm :
        The current EVM.
    amount :
        The amount of gas the current operation requires.

    """
    evm_trace(evm, GasAndRefund(int(amount)))

    if evm.gas_left < amount:
        raise OutOfGasError
    else:
        evm.gas_left -= amount


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
    size_in_words = ceil32(size_in_bytes) // Uint(32)
    linear_cost = size_in_words * GasCosts.MEMORY
    quadratic_cost = size_in_words ** Uint(2) // Uint(512)
    total_gas_cost = linear_cost + quadratic_cost
    try:
        return total_gas_cost
    except ValueError as e:
        raise OutOfGasError from e


def calculate_gas_extend_memory(
    memory: bytearray, extensions: List[Tuple[U256, U256]]
) -> ExtendMemory:
    """
    Calculates the gas amount to extend memory.

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    extensions:
        List of extensions to be made to the memory.
        Consists of a tuple of start position and size.

    Returns
    -------
    extend_memory: `ExtendMemory`

    """
    size_to_extend = Uint(0)
    to_be_paid = Uint(0)
    current_size = Uint(len(memory))
    for start_position, size in extensions:
        if size == 0:
            continue
        before_size = ceil32(current_size)
        after_size = ceil32(Uint(start_position) + Uint(size))
        if after_size <= before_size:
            continue

        size_to_extend += after_size - before_size
        already_paid = calculate_memory_gas_cost(before_size)
        total_cost = calculate_memory_gas_cost(after_size)
        to_be_paid += total_cost - already_paid

        current_size = after_size

    return ExtendMemory(to_be_paid, size_to_extend)


def calculate_message_call_gas(
    state: State, gas: Uint, to: Address, value: U256
) -> MessageCallGas:
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
    message_call_gas: `MessageCallGas`

    """
    create_gas_cost = (
        Uint(0) if account_exists(state, to) else GasCosts.NEW_ACCOUNT
    )
    transfer_gas_cost = Uint(0) if value == 0 else GasCosts.CALL_VALUE
    cost = GasCosts.CALL + gas + create_gas_cost + transfer_gas_cost
    stipend = gas if value == 0 else GasCosts.CALL_STIPEND + gas
    return MessageCallGas(cost, stipend)
