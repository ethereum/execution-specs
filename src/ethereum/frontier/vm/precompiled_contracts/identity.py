"""
Ethereum Virtual Machine (EVM) IDENTITY PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `IDENTITY` precompiled contract.
"""
from ethereum.base_types import Uint
from ethereum.utils.numeric import ceil32

from ...vm import Evm
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
    gas_fee = GAS_IDENTITY + word_count * GAS_IDENTITY_WORD
    evm.gas_left = subtract_gas(evm.gas_left, gas_fee)
    evm.output = data
