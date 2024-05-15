"""
Ethereum Virtual Machine (EVM) BLS12 381 CONTRACTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of pre-compiles in G1 (curve over base prime field).
"""
from typing import Tuple

from py_ecc.bls12_381.bls12_381_curve import (
    FQ,
    add,
    b,
    curve_order,
    is_on_curve,
    multiply,
)
from py_ecc.typing import Point2D

from ethereum.base_types import U256, Bytes, Uint

from ...vm import Evm
from ...vm.gas import charge_gas
from ...vm.memory import buffer_read
from ..exceptions import InvalidParameter

P = FQ.field_modulus


def bytes_to_G1(data: Bytes) -> Point2D:
    """
    Decode 128 bytes to a G1 point.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Point2D
        The G1 point.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.
    """
    assert len(data) == 128
    x = int.from_bytes(data[:64], "big")
    y = int.from_bytes(data[64:], "big")

    if x >= P:
        raise InvalidParameter("Invalid field element")
    if y >= P:
        raise InvalidParameter("Invalid field element")

    if x == 0 and y == 0:
        return None

    point = (FQ(x), FQ(y))

    # Check if the point is on the curve
    if not is_on_curve(point, b):
        raise InvalidParameter("Point is not on curve")

    return point


def G1_to_bytes(point: Point2D) -> Bytes:
    """
    Encode a G1 point to 128 bytes.

    Parameters
    ----------
    point :
        The G1 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    if point is None:
        return b"\x00" * 128

    x, y = point

    x_bytes = int(x).to_bytes(64, "big")
    y_bytes = int(y).to_bytes(64, "big")

    return x_bytes + y_bytes


def decode_G1_scalar_pair(data: Bytes) -> Tuple[Point2D, int]:
    """
    Decode 160 bytes to a G1 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Point2D, int]
        The G1 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the sub-group check failed.
    """
    assert len(data) == 160
    p = bytes_to_G1(buffer_read(data, U256(0), U256(128)))
    if multiply(p, curve_order) is not None:
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(128), U256(32)), "big")

    return p, m


def bls12_g1_add(evm: Evm) -> None:
    """
    The bls12_381 G1 point addition precompile.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid.
    """
    data = evm.message.data
    if len(data) != 256:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(500))

    # OPERATION
    p1 = bytes_to_G1(buffer_read(data, U256(0), U256(128)))
    p2 = bytes_to_G1(buffer_read(data, U256(128), U256(128)))

    result = add(p1, p2)

    evm.output = G1_to_bytes(result)


def bls12_g1_multiply(evm: Evm) -> None:
    """
    The bls12_381 G1 multiplication precompile.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid.
    """
    data = evm.message.data
    if len(data) != 160:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(12000))

    # OPERATION
    p, m = decode_G1_scalar_pair(data)
    result = multiply(p, m)

    evm.output = G1_to_bytes(result)
