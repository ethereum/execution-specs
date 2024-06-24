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
from dataclasses import dataclass
from typing import List, Tuple

from ethereum.base_types import U64, U256, Uint
from ethereum.trace import GasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32, taylor_exponential

from ..blocks import Header
from ..transactions import BlobTransaction, Transaction
from . import Evm
from .exceptions import OutOfGasError

GAS_JUMPDEST = Uint(1)
GAS_BASE = Uint(2)
GAS_VERY_LOW = Uint(3)
GAS_STORAGE_SET = Uint(20000)
GAS_STORAGE_UPDATE = Uint(5000)
GAS_STORAGE_CLEAR_REFUND = Uint(4800)
GAS_LOW = Uint(5)
GAS_MID = Uint(8)
GAS_HIGH = Uint(10)
GAS_EXPONENTIATION = Uint(10)
GAS_EXPONENTIATION_PER_BYTE = Uint(50)
GAS_MEMORY = Uint(3)
GAS_KECCAK256 = Uint(30)
GAS_KECCAK256_WORD = Uint(6)
GAS_COPY = Uint(3)
GAS_BLOCK_HASH = Uint(20)
GAS_LOG = Uint(375)
GAS_LOG_DATA = Uint(8)
GAS_LOG_TOPIC = Uint(375)
GAS_CREATE = Uint(32000)
GAS_CODE_DEPOSIT = Uint(200)
GAS_ZERO = Uint(0)
GAS_NEW_ACCOUNT = Uint(25000)
GAS_CALL_VALUE = Uint(9000)
GAS_CALL_STIPEND = Uint(2300)
GAS_SELF_DESTRUCT = Uint(5000)
GAS_SELF_DESTRUCT_NEW_ACCOUNT = Uint(25000)
GAS_ECRECOVER = Uint(3000)
GAS_SHA256 = Uint(60)
GAS_SHA256_WORD = Uint(12)
GAS_RIPEMD160 = Uint(600)
GAS_RIPEMD160_WORD = Uint(120)
GAS_IDENTITY = Uint(15)
GAS_IDENTITY_WORD = Uint(3)
GAS_RETURN_DATA_COPY = Uint(3)
GAS_FAST_STEP = Uint(5)
GAS_BLAKE2_PER_ROUND = Uint(1)
GAS_COLD_SLOAD = Uint(2100)
GAS_COLD_ACCOUNT_ACCESS = Uint(2600)
GAS_WARM_ACCESS = Uint(100)
GAS_INIT_CODE_WORD_COST = 2
GAS_BLOBHASH_OPCODE = Uint(3)
GAS_POINT_EVALUATION = Uint(50000)

TARGET_BLOB_GAS_PER_BLOCK = U64(393216)
GAS_PER_BLOB = Uint(2**17)
MIN_BLOB_GASPRICE = Uint(1)
BLOB_GASPRICE_UPDATE_FRACTION = Uint(3338477)


@dataclass
class ExtendMemory:
    """
    Define the parameters for memory extension in opcodes

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
    Define the gas cost and stipend for executing the call opcodes.

    `cost`: `ethereum.base_types.Uint`
        The non-refundable portion of gas reserved for executing the
        call opcode.
    `stipend`: `ethereum.base_types.Uint`
        The portion of gas available to sub-calls that is refundable
        if not consumed
    """

    cost: Uint
    stipend: Uint


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
    evm_trace(evm, GasAndRefund(amount))

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
    memory: bytearray, extensions: List[Tuple[U256, U256]]
) -> ExtendMemory:
    """
    Calculates the gas amount to extend memory

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
    value: U256,
    gas: Uint,
    gas_left: Uint,
    memory_cost: Uint,
    extra_gas: Uint,
    call_stipend: Uint = GAS_CALL_STIPEND,
) -> MessageCallGas:
    """
    Calculates the MessageCallGas (cost and stipend) for
    executing call Opcodes.

    Parameters
    ----------
    value:
        The amount of `ETH` that needs to be transferred.
    gas :
        The amount of gas provided to the message-call.
    gas_left :
        The amount of gas left in the current frame.
    memory_cost :
        The amount needed to extend the memory in the current frame.
    extra_gas :
        The amount of gas needed for transferring value + creating a new
        account inside a message call.
    call_stipend :
        The amount of stipend provided to a message call to execute code while
        transferring value(ETH).

    Returns
    -------
    message_call_gas: `MessageCallGas`
    """
    call_stipend = Uint(0) if value == 0 else call_stipend
    if gas_left < extra_gas + memory_cost:
        return MessageCallGas(gas + extra_gas, gas + call_stipend)

    gas = min(gas, max_message_call_gas(gas_left - memory_cost - extra_gas))

    return MessageCallGas(gas + extra_gas, gas + call_stipend)


def max_message_call_gas(gas: Uint) -> Uint:
    """
    Calculates the maximum gas that is allowed for making a message call

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.

    Returns
    -------
    max_allowed_message_call_gas: `ethereum.base_types.Uint`
        The maximum gas allowed for making the message-call.
    """
    return gas - (gas // 64)


def init_code_cost(init_code_length: Uint) -> Uint:
    """
    Calculates the gas to be charged for the init code in CREAT*
    opcodes as well as create transactions.

    Parameters
    ----------
    init_code_length :
        The length of the init code provided to the opcode
        or a create transaction

    Returns
    -------
    init_code_gas: `ethereum.base_types.Uint`
        The gas to be charged for the init code.
    """
    return GAS_INIT_CODE_WORD_COST * ceil32(init_code_length) // 32


def calculate_excess_blob_gas(parent_header: Header) -> U64:
    """
    Calculated the excess blob gas for the current block based
    on the gas used in the parent block.

    Parameters
    ----------
    parent_header :
        The parent block of the current block.

    Returns
    -------
    excess_blob_gas: `ethereum.base_types.U64`
        The excess blob gas for the current block.
    """
    parent_blob_gas = (
        parent_header.excess_blob_gas + parent_header.blob_gas_used
    )
    if parent_blob_gas < TARGET_BLOB_GAS_PER_BLOCK:
        return U64(0)
    else:
        return parent_blob_gas - TARGET_BLOB_GAS_PER_BLOCK


def calculate_total_blob_gas(tx: Transaction) -> Uint:
    """
    Calculate the total blob gas for a transaction.

    Parameters
    ----------
    tx :
        The transaction for which the blob gas is to be calculated.

    Returns
    -------
    total_blob_gas: `ethereum.base_types.Uint`
        The total blob gas for the transaction.
    """
    if isinstance(tx, BlobTransaction):
        return GAS_PER_BLOB * len(tx.blob_versioned_hashes)
    else:
        return Uint(0)


def calculate_blob_gas_price(excess_blob_gas: U64) -> Uint:
    """
    Calculate the blob gasprice for a block.

    Parameters
    ----------
    excess_blob_gas :
        The excess blob gas for the block.

    Returns
    -------
    blob_gasprice: `Uint`
        The blob gasprice.
    """
    return taylor_exponential(
        MIN_BLOB_GASPRICE,
        Uint(excess_blob_gas),
        BLOB_GASPRICE_UPDATE_FRACTION,
    )


def calculate_data_fee(excess_blob_gas: U64, tx: Transaction) -> Uint:
    """
    Calculate the blob data fee for a transaction.

    Parameters
    ----------
    excess_blob_gas :
        The excess_blob_gas for the execution.
    tx :
        The transaction for which the blob data fee is to be calculated.

    Returns
    -------
    data_fee: `Uint`
        The blob data fee.
    """
    return calculate_total_blob_gas(tx) * calculate_blob_gas_price(
        excess_blob_gas
    )
