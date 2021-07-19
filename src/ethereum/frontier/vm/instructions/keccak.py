"""
Ethereum Virtual Machine (EVM) Keccak Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM keccak instructions.
"""

from ethereum.base_types import U256, Uint
from ethereum.crypto import keccak256
from ethereum.utils import ceil32

from .. import Evm
from ..gas import (
    GAS_KECCAK256,
    GAS_KECCAK256_WORD,
    calculate_gas_extend_memory,
    subtract_gas,
)
from ..memory import extend_memory, memory_read_bytes
from ..stack import pop, push


def keccak(evm: Evm) -> None:
    """
    Pushes to the stack the Keccak-256 hash of a region of memory.

    This also expands the memory, in case the memory is insufficient to
    access the data's memory location.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    """
    # Converting memory_start_index to Uint as memory_end_index can
    # overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    size = pop(evm.stack)

    words = ceil32(Uint(size)) // 32
    gas_cost = (
        GAS_KECCAK256
        + (GAS_KECCAK256_WORD * words)
        + calculate_gas_extend_memory(evm.memory, memory_start_index, size)
    )
    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    extend_memory(evm.memory, memory_start_index, size)

    data = memory_read_bytes(evm.memory, memory_start_index, size)
    hash = keccak256(data)

    push(evm.stack, U256.from_be_bytes(hash))
