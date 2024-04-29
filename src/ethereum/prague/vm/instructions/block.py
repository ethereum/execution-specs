"""
Ethereum Virtual Machine (EVM) Block Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM block instructions.
"""

from ethereum.base_types import U256

from ...state import get_storage
from .. import Evm
from ..gas import GAS_BASE, GAS_COLD_SLOAD, GAS_WARM_ACCESS, charge_gas
from ..stack import pop, push


def block_hash(evm: Evm) -> None:
    """
    Push the hash of one of the 256 most recent complete blocks onto the
    stack. The block number to hash is present at the top of the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.prague.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `20`.
    """
    from ...fork import HISTORY_SERVE_WINDOW, HISTORY_STORAGE_ADDRESS

    # STACK
    block_number = pop(evm.stack)

    # GAS
    key = (block_number % HISTORY_SERVE_WINDOW).to_be_bytes32()
    if (HISTORY_STORAGE_ADDRESS, key) in evm.accessed_storage_keys:
        charge_gas(evm, GAS_WARM_ACCESS)
    else:
        evm.accessed_storage_keys.add((HISTORY_STORAGE_ADDRESS, key))
        charge_gas(evm, GAS_COLD_SLOAD)

    # OPERATION
    if (
        evm.env.number <= block_number
        or evm.env.number > block_number + HISTORY_SERVE_WINDOW
    ):
        # Default hash to 0, if the block of interest is not yet on the chain
        # (including the block which has the current executing transaction),
        # or if the block's age is more than HISTORY_SERVE_WINDOW.
        hash = b"\x00"
    else:
        hash = get_storage(
            evm.env.state,
            HISTORY_STORAGE_ADDRESS,
            key,
        ).to_be_bytes32()

    push(evm.stack, U256.from_be_bytes(hash))

    # PROGRAM COUNTER
    evm.pc += 1


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
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.env.coinbase))

    # PROGRAM COUNTER
    evm.pc += 1


def timestamp(evm: Evm) -> None:
    """
    Push the current block's timestamp onto the stack. Here the timestamp
    being referred is actually the unix timestamp in seconds.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, evm.env.time)

    # PROGRAM COUNTER
    evm.pc += 1


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
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(evm.env.number))

    # PROGRAM COUNTER
    evm.pc += 1


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
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256.from_be_bytes(evm.env.prev_randao))

    # PROGRAM COUNTER
    evm.pc += 1


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
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(evm.env.gas_limit))

    # PROGRAM COUNTER
    evm.pc += 1


def chain_id(evm: Evm) -> None:
    """
    Push the chain id onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.prague.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.prague.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(evm.env.chain_id))

    # PROGRAM COUNTER
    evm.pc += 1
