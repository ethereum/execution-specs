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
from ..gas import GAS_BASE, GAS_BLOCK_HASH, charge_gas
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `20`.
    """
    # STACK
    block_number = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_BLOCK_HASH)

    # OPERATION
    if evm.env.number <= block_number or evm.env.number > block_number + 256:
        # Default hash to 0, if the block of interest is not yet on the chain
        # (including the block which has the current executing transaction),
        # or if the block's age is more than 256.
        hash = b"\x00"
    else:
        hash = evm.env.block_hashes[-(evm.env.number - block_number)]

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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
    :py:class:`~ethereum.cancun.vm.exceptions.StackOverflowError`
        If `len(stack)` is equal to `1024`.
    :py:class:`~ethereum.cancun.vm.exceptions.OutOfGasError`
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
