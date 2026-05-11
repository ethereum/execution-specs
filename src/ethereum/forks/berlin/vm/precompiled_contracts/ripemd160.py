"""
Ethereum Virtual Machine (EVM) RIPEMD160 PRECOMPILED CONTRACT.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `RIPEMD160` precompiled contract.
"""

import hashlib

from ethereum_types.numeric import Uint, ulen

from ethereum.utils.byte import left_pad_zero_bytes
from ethereum.utils.numeric import ceil32

from ...vm import Evm
from ...vm.gas import (
    GasCosts,
    charge_gas,
)


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
    word_count = ceil32(ulen(data)) // Uint(32)
    charge_gas(
        evm,
        GasCosts.PRECOMPILE_RIPEMD160_BASE
        + GasCosts.PRECOMPILE_RIPEMD160_PER_WORD * word_count,
    )

    # OPERATION
    hash_bytes = hashlib.new("ripemd160", data).digest()
    padded_hash = left_pad_zero_bytes(hash_bytes, 32)
    evm.output = padded_hash
