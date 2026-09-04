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

from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.forks.bpo2.blocks import Header as PreviousHeader
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
    BASE: Final[Uint] = Uint(2)
    VERY_LOW: Final[Uint] = Uint(3)
    LOW: Final[Uint] = Uint(5)
    MID: Final[Uint] = Uint(8)
    HIGH: Final[Uint] = Uint(10)

    # Access
    WARM_ACCESS: Final[Uint] = Uint(100)
    COLD_ACCOUNT_ACCESS: Final[Uint] = Uint(2600)
    COLD_STORAGE_ACCESS: Final[Uint] = Uint(2100)

    # Storage
    STORAGE_SET: Final[Uint] = Uint(20000)
    COLD_STORAGE_WRITE: Final[Uint] = Uint(5000)

    # Call
    CALL_VALUE: Final[Uint] = Uint(9000)
    CALL_STIPEND: Final[Uint] = Uint(2300)
    NEW_ACCOUNT: Final[Uint] = Uint(25000)

    # Contract Creation
    CODE_DEPOSIT_PER_BYTE: Final[Uint] = Uint(200)
    CODE_INIT_PER_WORD: Final[Uint] = Uint(2)

    # Authorization
    AUTH_PER_EMPTY_ACCOUNT: Final[int] = 25000

    # Utility
    ZERO: Final[Uint] = Uint(0)
    MEMORY_PER_WORD: Final[Uint] = Uint(3)
    FAST_STEP: Final[Uint] = Uint(5)

    # Refunds
    REFUND_STORAGE_CLEAR: Final[int] = 4800

    # Precompiles
    PRECOMPILE_ECRECOVER: Final[Uint] = Uint(3000)
    PRECOMPILE_P256VERIFY: Final[Uint] = Uint(6900)
    PRECOMPILE_SHA256_BASE: Final[Uint] = Uint(60)
    PRECOMPILE_SHA256_PER_WORD: Final[Uint] = Uint(12)
    PRECOMPILE_RIPEMD160_BASE: Final[Uint] = Uint(600)
    PRECOMPILE_RIPEMD160_PER_WORD: Final[Uint] = Uint(120)
    PRECOMPILE_IDENTITY_BASE: Final[Uint] = Uint(15)
    PRECOMPILE_IDENTITY_PER_WORD: Final[Uint] = Uint(3)
    PRECOMPILE_BLAKE2F_PER_ROUND: Final[Uint] = Uint(1)
    PRECOMPILE_POINT_EVALUATION: Final[Uint] = Uint(50000)
    PRECOMPILE_BLS_G1ADD: Final[Uint] = Uint(375)
    PRECOMPILE_BLS_G1MUL: Final[Uint] = Uint(12000)
    PRECOMPILE_BLS_G1MAP: Final[Uint] = Uint(5500)
    PRECOMPILE_BLS_G2ADD: Final[Uint] = Uint(600)
    PRECOMPILE_BLS_G2MUL: Final[Uint] = Uint(22500)
    PRECOMPILE_BLS_G2MAP: Final[Uint] = Uint(23800)
    PRECOMPILE_ECADD: Final[Uint] = Uint(150)
    PRECOMPILE_ECMUL: Final[Uint] = Uint(6000)
    PRECOMPILE_ECPAIRING_BASE: Final[Uint] = Uint(45000)
    PRECOMPILE_ECPAIRING_PER_POINT: Final[Uint] = Uint(34000)

    # Blobs
    PER_BLOB: Final[U64] = U64(2**17)
    BLOB_SCHEDULE_TARGET: Final[U64] = U64(14)
    BLOB_TARGET_GAS_PER_BLOCK: Final[U64] = PER_BLOB * BLOB_SCHEDULE_TARGET
    BLOB_BASE_COST: Final[Uint] = Uint(2**13)
    BLOB_SCHEDULE_MAX: Final[U64] = U64(21)
    BLOB_MIN_GASPRICE: Final[Uint] = Uint(1)
    BLOB_BASE_FEE_UPDATE_FRACTION: Final[Uint] = Uint(11684671)

    # Transactions
    TX_BASE: Final[Uint] = Uint(21000)
    TX_CREATE: Final[Uint] = Uint(32000)
    TX_DATA_TOKEN_STANDARD: Final[Uint] = Uint(4)
    TX_DATA_TOKEN_FLOOR: Final[Uint] = Uint(10)
    TX_ACCESS_LIST_ADDRESS: Final[Uint] = Uint(2400)
    TX_ACCESS_LIST_STORAGE_KEY: Final[Uint] = Uint(1900)

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
    OPCODE_SHL: Final[Uint] = VERY_LOW
    OPCODE_SHR: Final[Uint] = VERY_LOW
    OPCODE_SAR: Final[Uint] = VERY_LOW
    OPCODE_CLZ: Final[Uint] = LOW
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
    OPCODE_PREVRANDAO: Final[Uint] = BASE
    OPCODE_RETURNDATASIZE: Final[Uint] = BASE
    OPCODE_CHAINID: Final[Uint] = BASE
    OPCODE_SELFBALANCE: Final[Uint] = FAST_STEP
    OPCODE_BASEFEE: Final[Uint] = BASE
    OPCODE_BLOBBASEFEE: Final[Uint] = BASE
    OPCODE_BLOBHASH: Final[Uint] = Uint(3)
    OPCODE_PUSH: Final[Uint] = VERY_LOW
    OPCODE_PUSH0: Final[Uint] = BASE
    OPCODE_DUP: Final[Uint] = VERY_LOW
    OPCODE_SWAP: Final[Uint] = VERY_LOW
    OPCODE_TLOAD: Final[Uint] = WARM_ACCESS
    OPCODE_TSTORE: Final[Uint] = WARM_ACCESS

    # Dynamic Opcodes
    OPCODE_RETURNDATACOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_RETURNDATACOPY_PER_WORD: Final[Uint] = Uint(3)
    OPCODE_CALLDATACOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_CODECOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_MCOPY_BASE: Final[Uint] = VERY_LOW
    OPCODE_MLOAD_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE_BASE: Final[Uint] = VERY_LOW
    OPCODE_MSTORE8_BASE: Final[Uint] = VERY_LOW
    OPCODE_COPY_PER_WORD: Final[Uint] = Uint(3)
    OPCODE_CREATE_BASE: Final[Uint] = Uint(32000)
    OPCODE_EXP_BASE: Final[Uint] = Uint(10)
    OPCODE_EXP_PER_BYTE: Final[Uint] = Uint(50)
    OPCODE_KECCAK256_BASE: Final[Uint] = Uint(30)
    OPCODE_KECCAK256_PER_WORD: Final[Uint] = Uint(6)
    OPCODE_LOG_BASE: Final[Uint] = Uint(375)
    OPCODE_LOG_DATA_PER_BYTE: Final[Uint] = Uint(8)
    OPCODE_LOG_TOPIC: Final[Uint] = Uint(375)
    OPCODE_SELFDESTRUCT_BASE: Final[Uint] = Uint(5000)
    OPCODE_SELFDESTRUCT_NEW_ACCOUNT: Final[Uint] = Uint(25000)


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


def calculate_excess_blob_gas(
    parent_header: Header | PreviousHeader,
) -> U64:
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
    # Defaults for a parent without blob gas fields.
    excess_blob_gas = U64(0)
    blob_gas_used = U64(0)
    base_fee_per_gas = Uint(0)

    if isinstance(parent_header, (Header, PreviousHeader)):
        # Read them from any parent that carries the fields, so
        # accumulated excess blob gas survives a fork transition.
        excess_blob_gas = parent_header.excess_blob_gas
        blob_gas_used = parent_header.blob_gas_used
        base_fee_per_gas = parent_header.base_fee_per_gas

    parent_blob_gas = excess_blob_gas + blob_gas_used
    if parent_blob_gas < GasCosts.BLOB_TARGET_GAS_PER_BLOCK:
        return U64(0)

    target_blob_gas_price = Uint(GasCosts.PER_BLOB)
    target_blob_gas_price *= calculate_blob_gas_price(excess_blob_gas)

    base_blob_tx_price = GasCosts.BLOB_BASE_COST * base_fee_per_gas
    if base_blob_tx_price > target_blob_gas_price:
        blob_schedule_delta = (
            GasCosts.BLOB_SCHEDULE_MAX - GasCosts.BLOB_SCHEDULE_TARGET
        )
        return (
            excess_blob_gas
            + blob_gas_used * blob_schedule_delta // GasCosts.BLOB_SCHEDULE_MAX
        )

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
