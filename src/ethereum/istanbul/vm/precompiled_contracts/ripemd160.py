"""
Ethereum Virtual Machine (EVM) RIPEMD160 PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `RIPEMD160` precompiled contract.
"""
import hashlib

from ethereum.base_types import Uint
from ethereum.utils.byte import left_pad_zero_bytes
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add, u256_safe_multiply

from ...vm import Evm
from ...vm.error import OutOfGasError
from ...vm.gas import GAS_RIPEMD160, GAS_RIPEMD160_WORD, subtract_gas


def ripemd160(evm: Evm) -> None:
    """
    Writes the ripemd160 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data
    word_count = ceil32(Uint(len(data))) // 32
    word_count_gas_cost = u256_safe_multiply(
        word_count,
        GAS_RIPEMD160_WORD,
        exception_type=OutOfGasError,
    )
    total_gas_cost = u256_safe_add(
        GAS_RIPEMD160,
        word_count_gas_cost,
        exception_type=OutOfGasError,
    )
    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)
    hash_bytes = hashlib.new("ripemd160", data).digest()
    padded_hash = left_pad_zero_bytes(hash_bytes, 32)
    evm.output = padded_hash
