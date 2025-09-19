"""
Ethereum Virtual Machine (EVM) ALT_BN128 CONTRACTS.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the ALT_BN128 precompiled contracts.
"""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint
from py_ecc.optimized_bn128.optimized_curve import (
    FQ,
    FQ2,
    FQ12,
    add,
    b,
    b2,
    curve_order,
    field_modulus,
    is_inf,
    is_on_curve,
    multiply,
    normalize,
)
from py_ecc.optimized_bn128.optimized_pairing import pairing
from py_ecc.typing import Optimized_Point3D as Point3D

from ...vm import Evm
from ...vm.gas import charge_gas
from ...vm.memory import buffer_read
from ..exceptions import InvalidParameter, OutOfGasError


def bytes_to_g1(data: Bytes) -> Point3D[FQ]:
    """
    Decode 64 bytes to a point on the curve.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Point3D
        A point on the curve.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.

    """
    if len(data) != 64:
        raise InvalidParameter("Input should be 64 bytes long")

    x_bytes = buffer_read(data, U256(0), U256(32))
    x = int(U256.from_be_bytes(x_bytes))
    y_bytes = buffer_read(data, U256(32), U256(32))
    y = int(U256.from_be_bytes(y_bytes))

    if x >= field_modulus:
        raise InvalidParameter("Invalid field element")
    if y >= field_modulus:
        raise InvalidParameter("Invalid field element")

    z = 1
    if x == 0 and y == 0:
        z = 0

    point = (FQ(x), FQ(y), FQ(z))

    # Check if the point is on the curve
    if not is_on_curve(point, b):
        raise InvalidParameter("Point is not on curve")

    return point


def bytes_to_g2(data: Bytes) -> Point3D[FQ2]:
    """
    Decode 128 bytes to a G2 point.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Point2D
        A point on the curve.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.

    """
    if len(data) != 128:
        raise InvalidParameter("G2 should be 128 bytes long")

    x0_bytes = buffer_read(data, U256(0), U256(32))
    x0 = int(U256.from_be_bytes(x0_bytes))
    x1_bytes = buffer_read(data, U256(32), U256(32))
    x1 = int(U256.from_be_bytes(x1_bytes))

    y0_bytes = buffer_read(data, U256(64), U256(32))
    y0 = int(U256.from_be_bytes(y0_bytes))
    y1_bytes = buffer_read(data, U256(96), U256(32))
    y1 = int(U256.from_be_bytes(y1_bytes))

    if x0 >= field_modulus or x1 >= field_modulus:
        raise InvalidParameter("Invalid field element")
    if y0 >= field_modulus or y1 >= field_modulus:
        raise InvalidParameter("Invalid field element")

    x = FQ2((x1, x0))
    y = FQ2((y1, y0))

    z = (1, 0)
    if x == FQ2((0, 0)) and y == FQ2((0, 0)):
        z = (0, 0)

    point = (x, y, FQ2(z))

    # Check if the point is on the curve
    if not is_on_curve(point, b2):
        raise InvalidParameter("Point is not on curve")

    return point


def alt_bn128_add(evm: Evm) -> None:
    """
    The ALT_BN128 addition precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(500))

    # OPERATION
    try:
        p0 = bytes_to_g1(buffer_read(data, U256(0), U256(64)))
        p1 = bytes_to_g1(buffer_read(data, U256(64), U256(64)))
    except InvalidParameter as e:
        raise OutOfGasError from e

    p = add(p0, p1)
    x, y = normalize(p)

    evm.output = Uint(x).to_be_bytes32() + Uint(y).to_be_bytes32()


def alt_bn128_mul(evm: Evm) -> None:
    """
    The ALT_BN128 multiplication precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(40000))

    # OPERATION
    try:
        p0 = bytes_to_g1(buffer_read(data, U256(0), U256(64)))
    except InvalidParameter as e:
        raise OutOfGasError from e
    n = int(U256.from_be_bytes(buffer_read(data, U256(64), U256(32))))

    p = multiply(p0, n)
    x, y = normalize(p)

    evm.output = Uint(x).to_be_bytes32() + Uint(y).to_be_bytes32()


def alt_bn128_pairing_check(evm: Evm) -> None:
    """
    The ALT_BN128 pairing check precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(80000 * (len(data) // 192) + 100000))

    # OPERATION
    if len(data) % 192 != 0:
        raise OutOfGasError
    result = FQ12.one()
    for i in range(len(data) // 192):
        try:
            p = bytes_to_g1(buffer_read(data, U256(192 * i), U256(64)))
            q = bytes_to_g2(buffer_read(data, U256(192 * i + 64), U256(128)))
        except InvalidParameter as e:
            raise OutOfGasError from e
        if not is_inf(multiply(p, curve_order)):
            raise OutOfGasError
        if not is_inf(multiply(q, curve_order)):
            raise OutOfGasError

        result *= pairing(q, p)

    if result == FQ12.one():
        evm.output = U256(1).to_be_bytes32()
    else:
        evm.output = U256(0).to_be_bytes32()
