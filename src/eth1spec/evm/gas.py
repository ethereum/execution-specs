"""
Ethereum Virtual Machine (EVM) Gas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""

from ..base_types import U256
from .error import OutOfGasError

GAS_VERY_LOW = U256(3)


def subtract_gas(gas_left: U256, amount: U256) -> U256:
    """
    Subtracts `amount` from `gas_left`.

    Parameters
    ----------
    gas_left :
        The amount of gas left in the current frame.
    amount :
        The amount of gas the current operation requires.

    Raises
    ------
    OutOfGasError
        If `gas_left` is less than `amount`.
    """
    if gas_left < amount:
        raise OutOfGasError

    return gas_left - amount
