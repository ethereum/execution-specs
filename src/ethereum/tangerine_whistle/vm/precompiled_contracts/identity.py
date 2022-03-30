"""
Ethereum Virtual Machine (EVM) IDENTITY PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `IDENTITY` precompiled contract.
"""
from ethereum.base_types import Uint
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...vm import Evm
from ...vm.error import OutOfGasError
from ...vm.gas import GAS_IDENTITY, GAS_IDENTITY_WORD, subtract_gas


def identity(evm: Evm) -> None:
    """
    Writes the message data to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data
    word_count = ceil32(Uint(len(data))) // 32
    word_count_gas_cost = u256_safe_multiply(
        word_count,
        GAS_IDENTITY_WORD,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_IDENTITY,
        word_count_gas_cost,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, total_gas_cost)
    evm.output = data
