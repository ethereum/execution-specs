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

from ...vm import Evm
from ...vm.gas import GAS_IDENTITY, GAS_IDENTITY_WORD, charge_gas


def identity(evm: Evm) -> None:
    """
    Writes the message data to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    word_count = ceil32(Uint(len(data))) // 32
    charge_gas(evm, GAS_IDENTITY + GAS_IDENTITY_WORD * word_count)

    # OPERATION
    evm.output = data
