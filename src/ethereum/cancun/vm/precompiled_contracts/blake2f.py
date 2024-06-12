"""
Ethereum Virtual Machine (EVM) Blake2 PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `Blake2` precompiled contract.
"""
from ethereum.crypto.blake2 import Blake2b

from ...vm import Evm
from ...vm.gas import GAS_BLAKE2_PER_ROUND, charge_gas
from ..exceptions import InvalidParameter


def blake2f(evm: Evm) -> None:
    """
    Writes the Blake2 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data
    if len(data) != 213:
        raise InvalidParameter

    blake2b = Blake2b()
    rounds, h, m, t_0, t_1, f = blake2b.get_blake2_parameters(data)

    charge_gas(evm, GAS_BLAKE2_PER_ROUND * rounds)
    if f not in [0, 1]:
        raise InvalidParameter

    evm.output = blake2b.compress(rounds, h, m, t_0, t_1, f)
