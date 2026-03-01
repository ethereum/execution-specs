"""
Ethereum Virtual Machine (EVM) BLS12 381 PAIRING PRE-COMPILE.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the BLS12 381 pairing pre-compile.
"""

from ethereum_types.numeric import Uint

from ethereum.crypto.bls12_381 import pairing_check

from ....vm import Evm
from ....vm.gas import charge_gas
from ...exceptions import InvalidParameter
from . import unpad_g1, unpad_g2


def bls12_pairing(evm: Evm) -> None:
    """
    The bls12_381 pairing precompile.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid or if the subgroup check
        fails.

    """
    data = evm.message.data
    if len(data) == 0 or len(data) % 384 != 0:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    k = len(data) // 384
    gas_cost = Uint(32600 * k + 37700)
    charge_gas(evm, gas_cost)

    # OPERATION
    g1_points = []
    g2_points = []
    for i in range(k):
        g1_start = 384 * i
        g2_start = 384 * i + 128

        g1_points.append(unpad_g1(data[g1_start : g1_start + 128]))
        g2_points.append(unpad_g2(data[g2_start : g2_start + 256]))

    try:
        result = pairing_check(g1_points, g2_points)
    except ValueError as e:
        raise InvalidParameter(str(e)) from None

    if result:
        evm.output = b"\x00" * 31 + b"\x01"
    else:
        evm.output = b"\x00" * 32
