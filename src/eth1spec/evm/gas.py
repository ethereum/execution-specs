"""
EVM Gas Constants and Calculators
"""
from ..eth_types import Uint
from .error import OutOfGasError

GAS_VERY_LOW = Uint(3)


def subtract_gas(gas_left: Uint, amount: Uint) -> Uint:
    """
    Subtracts `amount` from `gas_left`.

    Parameters
    ----------
    gas_left : `Uint`
        The amount of gas left in the current frame.
    amount : `Uint`
        The amount of gas the current operation requires.

    Raises
    ------
    OutOfGasError
        If `gas_left` is less than `amount`.
    """
    if gas_left < amount:
        raise OutOfGasError

    return gas_left - amount
