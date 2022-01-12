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

from .. import Evm
from ..gas import GAS_BASE, GAS_BLOCK_HASH, subtract_gas
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
    :py:class:`~ethereum.dao_fork.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `20`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BLOCK_HASH)

    block_number = pop(evm.stack)

    if evm.env.number <= block_number or evm.env.number > block_number + 256:
        # Default hash to 0, if the block of interest is not yet on the chain
        # (including the block which has the current executing transaction),
        # or if the block's age is more than 256.
        hash = b"\x00"
    else:
        hash = evm.env.block_hashes[-(evm.env.number - block_number)]

    push(evm.stack, U256.from_be_bytes(hash))

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
    :py:class:`~ethereum.dao_fork.vm.error.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256.from_be_bytes(evm.env.coinbase))

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
    :py:class:`~ethereum.dao_fork.vm.error.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, evm.env.time)

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
    :py:class:`~ethereum.dao_fork.vm.error.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(evm.env.number))

    evm.pc += 1


def difficulty(evm: Evm) -> None:
    """
    Push the current block's difficulty onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.dao_fork.vm.error.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(evm.env.difficulty))

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
    :py:class:`~ethereum.dao_fork.vm.error.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.dao_fork.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(evm.env.gas_limit))

    evm.pc += 1
