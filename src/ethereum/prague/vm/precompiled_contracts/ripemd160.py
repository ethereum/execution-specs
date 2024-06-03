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

from ...vm import Evm
from ...vm.gas import GAS_RIPEMD160, GAS_RIPEMD160_WORD, charge_gas


def ripemd160(evm: Evm) -> None:
    """
    Writes the ripemd160 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    word_count = ceil32(Uint(len(data))) // 32
    charge_gas(evm, GAS_RIPEMD160 + GAS_RIPEMD160_WORD * word_count)

    # OPERATION
    hash_bytes = hashlib.new("ripemd160", data).digest()
    padded_hash = left_pad_zero_bytes(hash_bytes, 32)
    evm.output = padded_hash
