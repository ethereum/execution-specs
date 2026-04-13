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

from ethereum_types.numeric import U64, U256, Uint

from ethereum.trace import GasAndRefund, evm_trace
from ethereum.utils.numeric import ceil32, taylor_exponential

from ..blocks import Header
from ..transactions import BlobTransaction, Transaction
from . import Evm
from .exceptions import OutOfGasError


# These values may be patched at runtime by a future gas repricing utility
class GasCosts:
    """
    Constant gas values for the EVM.
    """

    # Tiers
    BASE = Uint(2)
    VERY_LOW = Uint(3)
    LOW = Uint(5)
    MID = Uint(8)
    HIGH = Uint(10)

    # Access
    WARM_ACCESS = Uint(100)
    COLD_ACCOUNT_ACCESS = Uint(2600)
    COLD_STORAGE_ACCESS = Uint(2100)

    # Storage
    STORAGE_SET = Uint(20000)
    COLD_STORAGE_WRITE = Uint(5000)

    # Call
    CALL_VALUE = Uint(9000)
    CALL_STIPEND = Uint(2300)
    NEW_ACCOUNT = Uint(25000)

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE = Uint(200)
    CODE_INIT_PER_WORD = Uint(2)

    # Utility
    ZERO = Uint(0)
    MEMORY_PER_WORD = Uint(3)
    FAST_STEP = Uint(5)

    # Refunds
    REFUND_STORAGE_CLEAR = 4800

    # Precompiles
    PRECOMPILE_ECRECOVER = Uint(3000)
    PRECOMPILE_SHA256_BASE = Uint(60)
    PRECOMPILE_SHA256_PER_WORD = Uint(12)
    PRECOMPILE_RIPEMD160_BASE = Uint(600)
    PRECOMPILE_RIPEMD160_PER_WORD = Uint(120)
    PRECOMPILE_IDENTITY_BASE = Uint(15)
    PRECOMPILE_IDENTITY_PER_WORD = Uint(3)
    PRECOMPILE_BLAKE2F_PER_ROUND = Uint(1)
    PRECOMPILE_POINT_EVALUATION = Uint(50000)
    PRECOMPILE_ECADD = Uint(150)
    PRECOMPILE_ECMUL = Uint(6000)
    PRECOMPILE_ECPAIRING_BASE = Uint(45000)
    PRECOMPILE_ECPAIRING_PER_POINT = Uint(34000)

    # Blobs
    PER_BLOB = U64(2**17)
    BLOB_TARGET_GAS_PER_BLOCK = U64(393216)
    BLOB_MIN_GASPRICE = Uint(1)
    BLOB_BASE_FEE_UPDATE_FRACTION = Uint(3338477)

    # Transactions
    TX_BASE = Uint(21000)
    TX_CREATE = Uint(32000)
    TX_DATA_PER_ZERO = Uint(4)
    TX_DATA_PER_NON_ZERO = Uint(16)
    TX_ACCESS_LIST_ADDRESS = Uint(2400)
    TX_ACCESS_LIST_STORAGE_KEY = Uint(1900)

    # Block
    LIMIT_ADJUSTMENT_FACTOR = Uint(1024)
    LIMIT_MINIMUM = Uint(5000)

    # Static Opcodes
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
    OPCODE_SHL = VERY_LOW
    OPCODE_SHR = VERY_LOW
    OPCODE_SAR = VERY_LOW
    OPCODE_JUMP = MID
    OPCODE_JUMPI = HIGH
    OPCODE_JUMPDEST = Uint(1)
    OPCODE_CALLDATALOAD = VERY_LOW
    OPCODE_BLOCKHASH = Uint(20)
    OPCODE_COINBASE = BASE
    OPCODE_POP = BASE
    OPCODE_MSIZE = BASE
    OPCODE_PC = BASE
    OPCODE_GAS = BASE
    OPCODE_ADDRESS = BASE
    OPCODE_ORIGIN = BASE
    OPCODE_CALLER = BASE
    OPCODE_CALLVALUE = BASE
    OPCODE_CALLDATASIZE = BASE
    OPCODE_CODESIZE = BASE
    OPCODE_GASPRICE = BASE
    OPCODE_TIMESTAMP = BASE
    OPCODE_NUMBER = BASE
    OPCODE_GASLIMIT = BASE
    OPCODE_PREVRANDAO = BASE
    OPCODE_RETURNDATASIZE = BASE
    OPCODE_CHAINID = BASE
    OPCODE_BASEFEE = BASE
    OPCODE_BLOBBASEFEE = BASE
    OPCODE_BLOBHASH = Uint(3)
    OPCODE_PUSH = VERY_LOW
    OPCODE_PUSH0 = BASE
    OPCODE_DUP = VERY_LOW
    OPCODE_SWAP = VERY_LOW

    # Dynamic Opcodes
    OPCODE_RETURNDATACOPY_BASE = VERY_LOW
    OPCODE_RETURNDATACOPY_PER_WORD = Uint(3)
    OPCODE_CALLDATACOPY_BASE = VERY_LOW
    OPCODE_CODECOPY_BASE = VERY_LOW
    OPCODE_MCOPY_BASE = VERY_LOW
    OPCODE_MLOAD_BASE = VERY_LOW
    OPCODE_MSTORE_BASE = VERY_LOW
    OPCODE_MSTORE8_BASE = VERY_LOW
    OPCODE_COPY_PER_WORD = Uint(3)
    OPCODE_CREATE_BASE = Uint(32000)
    OPCODE_EXP_BASE = Uint(10)
    OPCODE_EXP_PER_BYTE = Uint(50)
    OPCODE_KECCAK256_BASE = Uint(30)
    OPCODE_KECCACK256_PER_WORD = Uint(6)
    OPCODE_LOG_BASE = Uint(375)
    OPCODE_LOG_DATA_PER_BYTE = Uint(8)
    OPCODE_LOG_TOPIC = Uint(375)
    OPCODE_SELFDESTRUCT_BASE = Uint(5000)
    OPCODE_SELFDESTRUCT_NEW_ACCOUNT = Uint(25000)


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
    call_stipend: Uint = GasCosts.CALL_STIPEND,
) -> MessageCallGas:
    """
    Calculates the MessageCallGas (cost and gas made available to the sub-call)
    for executing call Opcodes.

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
        transferring value (ETH).

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
    Calculates the maximum gas that is allowed for making a message call.

    Parameters
    ----------
    gas :
        The amount of gas provided to the message-call.

    Returns
    -------
    max_allowed_message_call_gas: `ethereum.base_types.Uint`
        The maximum gas allowed for making the message-call.

    """
    return gas - (gas // Uint(64))


def init_code_cost(init_code_length: Uint) -> Uint:
    """
    Calculates the gas to be charged for the init code in CREATE*
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
    return GasCosts.CODE_INIT_PER_WORD * ceil32(init_code_length) // Uint(32)


def calculate_excess_blob_gas(parent_header: Header) -> U64:
    """
    Calculates the excess blob gas for the current block based
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
    # At the fork block, these are defined as zero.
    excess_blob_gas = U64(0)
    blob_gas_used = U64(0)

    if isinstance(parent_header, Header):
        # After the fork block, read them from the parent header.
        excess_blob_gas = parent_header.excess_blob_gas
        blob_gas_used = parent_header.blob_gas_used

    parent_blob_gas = excess_blob_gas + blob_gas_used
    if parent_blob_gas < GasCosts.BLOB_TARGET_GAS_PER_BLOCK:
        return U64(0)

    return parent_blob_gas - GasCosts.BLOB_TARGET_GAS_PER_BLOCK


def calculate_total_blob_gas(tx: Transaction) -> U64:
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
        return GasCosts.PER_BLOB * U64(len(tx.blob_versioned_hashes))
    else:
        return U64(0)


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
        GasCosts.BLOB_MIN_GASPRICE,
        Uint(excess_blob_gas),
        GasCosts.BLOB_BASE_FEE_UPDATE_FRACTION,
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
    return Uint(calculate_total_blob_gas(tx)) * calculate_blob_gas_price(
        excess_blob_gas
    )
