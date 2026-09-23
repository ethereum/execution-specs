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
from typing import Final, List, Tuple, final

from ethereum_types.numeric import U256, Uint, ulen

from ethereum.state import Address
from ethereum.trace import GasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32

from ..state_tracker import TransactionState, account_exists
from . import Evm
from .exceptions import OutOfGasError


# These values may be patched at runtime by a future gas repricing utility
class GasCosts:
    """
    Constant gas values for the EVM.
    """

    # Tiers
    BASE: Final[Uint] = Uint(2)
    VERY_LOW: Final[Uint] = Uint(3)
    LOW: Final[Uint] = Uint(5)
    MID: Final[Uint] = Uint(8)
    HIGH: Final[Uint] = Uint(10)

    # Access
    SLOAD: Final[Uint] = Uint(50)

    # Storage
    STORAGE_SET: Final[Uint] = Uint(20000)
    COLD_STORAGE_WRITE: Final[Uint] = Uint(5000)

    # Call
    CALL_STIPEND: Final[Uint] = Uint(2300)
    CALL_VALUE: Final[Uint] = Uint(9000)
    NEW_ACCOUNT: Final[Uint] = Uint(25000)

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE: Final[Uint] = Uint(200)

    # Utility
    ZERO: Final[Uint] = Uint(0)
    MEMORY_PER_WORD: Final[Uint] = Uint(3)

    # Refunds
    REFUND_STORAGE_CLEAR: Final[int] = 15000
    REFUND_SELF_DESTRUCT: Final[Uint] = Uint(24000)

    # Precompiles
    PRECOMPILE_ECRECOVER: Final[Uint] = Uint(3000)
    PRECOMPILE_SHA256_BASE: Final[Uint] = Uint(60)
    PRECOMPILE_SHA256_PER_WORD: Final[Uint] = Uint(12)
    PRECOMPILE_RIPEMD160_BASE: Final[Uint] = Uint(600)
    PRECOMPILE_RIPEMD160_PER_WORD: Final[Uint] = Uint(120)
    PRECOMPILE_IDENTITY_BASE: Final[Uint] = Uint(15)
    PRECOMPILE_IDENTITY_PER_WORD: Final[Uint] = Uint(3)

    # Transactions
    TX_BASE: Final[Uint] = Uint(21000)
    TX_CREATE: Final[Uint] = Uint(32000)
    TX_DATA_PER_ZERO: Final[Uint] = Uint(4)
    TX_DATA_PER_NON_ZERO: Final[Uint] = Uint(68)

    # Block
    LIMIT_ADJUSTMENT_FACTOR: Final[Uint] = Uint(1024)
    LIMIT_MINIMUM: Final[Uint] = Uint(5000)

    # Static Opcodes
    OPCODE_ADD: Final[Uint] = VERY_LOW
    OPCODE_SUB: Final[Uint] = VERY_LOW
    OPCODE_MUL: Final[Uint] = LOW
    OPCODE_DIV: Final[Uint] = LOW
    OPCODE_SDIV: Final[Uint] = LOW
    OPCODE_MOD: Final[Uint] = LOW
    OPCODE_SMOD: Final[Uint] = LOW
    OPCODE_ADDMOD: Final[Uint] = MID
    OPCODE_MULMOD: Final[Uint] = MID
    OPCODE_SIGNEXTEND: Final[Uint] = LOW
    OPCODE_LT: Final[Uint] = VERY_LOW
    OPCODE_GT: Final[Uint] = VERY_LOW
    OPCODE_SLT: Final[Uint] = VERY_LOW
    OPCODE_SGT: Final[Uint] = VERY_LOW
    OPCODE_EQ: Final[Uint] = VERY_LOW
    OPCODE_ISZERO: Final[Uint] = VERY_LOW
    OPCODE_AND: Final[Uint] = VERY_LOW
    OPCODE_OR: Final[Uint] = VERY_LOW
    OPCODE_XOR: Final[Uint] = VERY_LOW
    OPCODE_NOT: Final[Uint] = VERY_LOW
    OPCODE_BYTE: Final[Uint] = VERY_LOW
    OPCODE_JUMP: Final[Uint] = MID
    OPCODE_JUMPI: Final[Uint] = HIGH
    OPCODE_JUMPDEST: Final[Uint] = Uint(1)
    OPCODE_CALLDATALOAD: Final[Uint] = VERY_LOW
    OPCODE_BLOCKHASH: Final[Uint] = Uint(20)
    OPCODE_COINBASE: Final[Uint] = BASE
    OPCODE_POP: Final[Uint] = BASE
    OPCODE_MSIZE: Final[Uint] = BASE
    OPCODE_PC: Final[Uint] = BASE
    OPCODE_GAS: Final[Uint] = BASE
    OPCODE_ADDRESS: Final[Uint] = BASE
    OPCODE_ORIGIN: Final[Uint] = BASE
    OPCODE_CALLER: Final[Uint] = BASE
    OPCODE_CALLVALUE: Final[Uint] = BASE
    OPCODE_CALLDATASIZE: Final[Uint] = BASE
    OPCODE_CODESIZE: Final[Uint] = BASE
    OPCODE_GASPRICE: Final[Uint] = BASE
    OPCODE_TIMESTAMP: Final[Uint] = BASE
    OPCODE_NUMBER: Final[Uint] = BASE
    OPCODE_GASLIMIT: Final[Uint] = BASE
    OPCODE_DIFFICULTY: Final[Uint] = BASE
    OPCODE_PUSH: Final[Uint] = VERY_LOW
    OPCODE_DUP: Final[Uint] = VERY_LOW
    OPCODE_SWAP: Final[Uint] = VERY_LOW

    # Dynamic Opcodes
    OPCODE_CALLDATACOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_CODECOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_MLOAD_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE8_BASE: Final[Uint] = VERY_LOW
    OPCODE_COPY_PER_WORD: Final[Uint] = Uint(3)
    OPCODE_CREATE_BASE: Final[Uint] = Uint(32000)
    OPCODE_EXP_BASE: Final[Uint] = Uint(10)
    OPCODE_EXP_PER_BYTE: Final[Uint] = Uint(10)
    OPCODE_KECCAK256_BASE: Final[Uint] = Uint(30)
    OPCODE_KECCAK256_PER_WORD: Final[Uint] = Uint(6)
    OPCODE_LOG_BASE: Final[Uint] = Uint(375)
    OPCODE_LOG_DATA_PER_BYTE: Final[Uint] = Uint(8)
    OPCODE_LOG_TOPIC: Final[Uint] = Uint(375)
    OPCODE_EXTERNAL_BASE: Final[Uint] = Uint(20)
    OPCODE_BALANCE: Final[Uint] = Uint(20)
    OPCODE_CALL_BASE: Final[Uint] = Uint(40)


@final
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


@final
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
    linear_cost = size_in_words * GasCosts.MEMORY_PER_WORD
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
    current_size = ulen(memory)
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
    state: TransactionState, gas: Uint, to: Address, value: U256
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
    cost = (
        GasCosts.OPCODE_CALL_BASE + gas + create_gas_cost + transfer_gas_cost
    )
    stipend = gas if value == 0 else GasCosts.CALL_STIPEND + gas
    return MessageCallGas(cost, stipend)
