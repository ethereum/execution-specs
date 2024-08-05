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

from ...vm import Evm
from ...vm.gas import GAS_SHA256, GAS_SHA256_WORD, charge_gas


def sha256(evm: Evm) -> None:
    """
    Writes the sha256 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    word_count = ceil32(Uint(len(data))) // 32
    charge_gas(evm, GAS_SHA256 + GAS_SHA256_WORD * word_count)

    # OPERATION
    evm.output = hashlib.sha256(data).digest()
