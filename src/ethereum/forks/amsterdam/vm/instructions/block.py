"""
Ethereum Virtual Machine (EVM) Block Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM block instructions.
"""

from ethereum_types.numeric import U256, Uint

from ...state_tracker import get_storage
from ...utils.hexadecimal import hex_to_address
from .. import Evm
from ..gas import GasCosts, charge_gas
from ..stack import pop, push

HISTORY_STORAGE_ADDRESS = hex_to_address(
    "0x0000F90827F1C53a10cb7A02335B175320002935"
)
HISTORY_SERVE_WINDOW = Uint(8191)
BLOCKHASH_SERVE_WINDOW = Uint(256)


def block_hash(evm: Evm) -> None:
    """
    Push the hash of one of the 256 most recent complete blocks onto the
    stack. The block number to hash is present at the top of the stack.

    The hash is read from the history storage contract using SLOAD
    semantics for gas accounting and storage slot warming.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than the gas required for `BLOCKHASH`:
        the base opcode cost, plus cold or warm history-slot access cost
        for valid in-range queries.

    """
    # STACK
    block_number = Uint(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_BLOCKHASH)

    # OPERATION
    current_block_number = evm.block_env.number
    max_block_number = block_number + BLOCKHASH_SERVE_WINDOW
    if (
        current_block_number <= block_number
        or current_block_number > max_block_number
    ):
        push(evm.stack, U256(0))
        evm.pc += Uint(1)
        return

    storage_slot = U256(block_number % HISTORY_SERVE_WINDOW)
    storage_key = storage_slot.to_be_bytes32()
    if (
        HISTORY_STORAGE_ADDRESS,
        storage_key,
    ) in evm.accessed_storage_keys:
        charge_gas(evm, GasCosts.WARM_ACCESS)
    else:
        evm.accessed_storage_keys.add((HISTORY_STORAGE_ADDRESS, storage_key))
        charge_gas(evm, GasCosts.COLD_STORAGE_ACCESS)

    tx_state = evm.tx_env.state
    hash_value = get_storage(
        tx_state,
        HISTORY_STORAGE_ADDRESS,
        storage_key,
    )

    push(evm.stack, hash_value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def coinbase(evm: Evm) -> None:
    """
    Push the current block's beneficiary address (address of the block miner)
    onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_COINBASE)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.block_env.coinbase))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def timestamp(evm: Evm) -> None:
    """
    Push the current block's timestamp onto the stack. Here the timestamp
    being referred to is actually the unix timestamp in seconds.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_TIMESTAMP)

    # OPERATION
    push(evm.stack, evm.block_env.time)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def number(evm: Evm) -> None:
    """
    Push the current block's number onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_NUMBER)

    # OPERATION
    push(evm.stack, U256(evm.block_env.number))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def prev_randao(evm: Evm) -> None:
    """
    Push the `prev_randao` value onto the stack.

    The `prev_randao` value is the random output of the beacon chain's
    randomness oracle for the previous block.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_PREVRANDAO)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.block_env.prev_randao))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def gas_limit(evm: Evm) -> None:
    """
    Push the current block's gas limit onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_GASLIMIT)

    # OPERATION
    push(evm.stack, U256(evm.block_env.block_gas_limit))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def chain_id(evm: Evm) -> None:
    """
    Push the chain id onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CHAINID)

    # OPERATION
    push(evm.stack, U256(evm.block_env.chain_id))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def slot_number(evm: Evm) -> None:
    """
    Push the current slot number onto the stack.

    The slot number is provided by the consensus layer and passed to the
    execution layer through the engine API.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.forks.amsterdam.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SLOTNUM)

    # OPERATION
    push(evm.stack, U256(evm.block_env.slot_number))

    # PROGRAM COUNTER
    evm.pc += Uint(1)
