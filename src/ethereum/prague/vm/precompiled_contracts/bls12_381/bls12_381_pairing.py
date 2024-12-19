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
from py_ecc.bls12_381.bls12_381_curve import FQ12, curve_order, multiply
from py_ecc.bls12_381.bls12_381_pairing import pairing

from ethereum.base_types import U256, Uint

from ....vm import Evm
from ....vm.gas import charge_gas
from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter
from . import bytes_to_G1, bytes_to_G2


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

        g1_point = bytes_to_G1(buffer_read(data, U256(g1_start), U256(128)))
        if multiply(g1_point, curve_order) is not None:
            raise InvalidParameter("Sub-group check failed.")

        g2_point = bytes_to_G2(buffer_read(data, U256(g2_start), U256(256)))
        if multiply(g2_point, curve_order) is not None:
            raise InvalidParameter("Sub-group check failed.")

        result *= pairing(g2_point, g1_point)

    if result == FQ12.one():
        evm.output = b"\x00" * 31 + b"\x01"
    else:
        evm.output = b"\x00" * 32
