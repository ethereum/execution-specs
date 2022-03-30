"""
Ethereum Virtual Machine (EVM) SHA256 PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `SHA256` precompiled contract.
"""
import hashlib

from ethereum.base_types import Uint
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...vm import Evm
from ...vm.error import OutOfGasError
from ...vm.gas import GAS_SHA256, GAS_SHA256_WORD, subtract_gas


def sha256(evm: Evm) -> None:
    """
    Writes the sha256 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data
    word_count = ceil32(Uint(len(data))) // 32
    word_count_gas_cost = u256_safe_multiply(
        word_count,
        GAS_SHA256_WORD,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_SHA256,
        word_count_gas_cost,
        exception_type=OutOfGasError,
    )
    subtract_gas(evm, total_gas_cost)
    evm.output = hashlib.sha256(data).digest()
