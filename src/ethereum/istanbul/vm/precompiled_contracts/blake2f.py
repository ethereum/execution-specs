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
from ethereum.utils.ensure import ensure

from ...vm import Evm
from ...vm.error import InvalidParameter
from ...vm.gas import GAS_BLAKE2_PER_ROUND, subtract_gas


def blake2f(evm: Evm) -> None:
    """
    Writes the Blake2 hash to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    ensure(len(data) == 213, InvalidParameter)

    blake2b = Blake2b()
    rounds, h, m, t_0, t_1, f = blake2b.get_blake2_parameters(data)

    ensure(f in [0, 1], InvalidParameter)

    total_gas_cost = GAS_BLAKE2_PER_ROUND * rounds

    evm.gas_left = subtract_gas(evm.gas_left, total_gas_cost)

    evm.output = blake2b.compress(rounds, h, m, t_0, t_1, f)
