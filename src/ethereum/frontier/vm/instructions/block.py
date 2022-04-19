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
from typing import List

from ethereum.base_types import U256

from .. import Evm
from ..gas import GAS_BASE, GAS_BLOCK_HASH
from ..operation import Operation, static_gas


def do_block_hash(evm: Evm, stack: List[U256], block_number: U256) -> U256:
    """
    Push the hash of one of the 256 most recent complete blocks onto the
    stack. The block number to hash is present at the top of the stack.
    """
    if evm.env.number <= block_number or evm.env.number > block_number + 256:
        # Default hash to 0, if the block of interest is not yet on the chain
        # (including the block which has the current executing transaction),
        # or if the block's age is more than 256.
        return U256(0)
    else:
        return U256.from_be_bytes(
            evm.env.block_hashes[-(evm.env.number - block_number)]
        )


block_hash = Operation(static_gas(GAS_BLOCK_HASH), do_block_hash, 1, 1)


def do_coinbase(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the current block's beneficiary address (address of the block miner)
    onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.
    """
    return U256.from_be_bytes(evm.env.coinbase)


coinbase = Operation(static_gas(GAS_BASE), do_coinbase, 0, 1)


def do_timestamp(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the current block's timestamp onto the stack. Here the timestamp
    being referred is actually the unix timestamp in seconds.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.
    """
    return evm.env.time


timestamp = Operation(static_gas(GAS_BASE), do_timestamp, 0, 1)


def do_number(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the current block's number onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.
    """
    return U256(evm.env.number)


number = Operation(static_gas(GAS_BASE), do_number, 0, 1)


def do_difficulty(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the current block's difficulty onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.
    """
    return U256(evm.env.difficulty)


difficulty = Operation(static_gas(GAS_BASE), do_difficulty, 0, 1)


def do_gas_limit(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the current block's gas limit onto the stack.

    Here the current block refers to the block in which the currently
    executing transaction/call resides.
    """
    return U256(evm.env.gas_limit)


gas_limit = Operation(static_gas(GAS_BASE), do_gas_limit, 0, 1)
