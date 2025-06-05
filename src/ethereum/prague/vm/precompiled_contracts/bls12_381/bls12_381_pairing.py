"""
Ethereum Virtual Machine (EVM) BLS12 381 PAIRING PRE-COMPILE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the BLS12 381 pairing pre-compile.
"""

from ethereum_types.numeric import Uint
from py_ecc.optimized_bls12_381 import FQ12, curve_order, is_inf
from py_ecc.optimized_bls12_381 import multiply as bls12_multiply_optimized
from py_ecc.optimized_bls12_381 import pairing

from ....vm import Evm
from ....vm.gas import charge_gas
from ...exceptions import InvalidParameter
from . import bytes_to_g1, bytes_to_g2


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
        If the input length is invalid or if sub-group check fails.
    """
    data = evm.message.data
    if len(data) == 0 or len(data) % 384 != 0:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    k = len(data) // 384
    gas_cost = Uint(32600 * k + 37700)
    charge_gas(evm, gas_cost)

    # OPERATION
    result = FQ12.one()
    for i in range(k):
        g1_start = Uint(384 * i)
        g2_start = Uint(384 * i + 128)

        g1_point = bytes_to_g1(data[g1_start : g1_start + Uint(128)])
        if not is_inf(bls12_multiply_optimized(g1_point, curve_order)):
            raise InvalidParameter("Sub-group check failed for G1 point.")

        g2_point = bytes_to_g2(data[g2_start : g2_start + Uint(256)])
        if not is_inf(bls12_multiply_optimized(g2_point, curve_order)):
            raise InvalidParameter("Sub-group check failed for G2 point.")

        result *= pairing(g2_point, g1_point)

    if result == FQ12.one():
        evm.output = b"\x00" * 31 + b"\x01"
    else:
        evm.output = b"\x00" * 32
