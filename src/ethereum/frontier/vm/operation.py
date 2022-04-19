"""
Operation
^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Dataclass representing EVM operations.
"""

from dataclasses import dataclass
from typing import Any, Callable

from ethereum.base_types import U256

from . import Evm
from .gas import subtract_gas


@dataclass
class Operation:
    """
    An EVM operation.
    """

    charge_gas: Callable
    do: Callable
    args: int
    results: int
    length: int = 1


def static_gas(amount: U256) -> Callable:
    """
    Return a `charge_gas` function for an operation that uses a static amount
    of gas.
    """

    def fun(evm: Evm, *args: Any) -> None:
        subtract_gas(evm, amount)

    return fun
