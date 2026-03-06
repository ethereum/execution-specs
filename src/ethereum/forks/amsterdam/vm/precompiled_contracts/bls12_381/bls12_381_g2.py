"""
Ethereum Virtual Machine (EVM) BLS12 381 G2 CONTRACTS.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of pre-compiles in G2 (curve over base prime field).
"""

from ethereum_types.numeric import U256, Uint

from ethereum.crypto.bls12_381 import g2_add, g2_msm, map_fp2_to_g2

from ....vm import Evm
from ....vm.gas import (
    GAS_BLS_G2_ADD,
    GAS_BLS_G2_MAP,
    GAS_BLS_G2_MUL,
    charge_gas,
)
from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter
from . import (
    G2_K_DISCOUNT,
    G2_MAX_DISCOUNT,
    MULTIPLIER,
    pad_g2,
    unpad_fp,
    unpad_g2,
)

LENGTH_PER_PAIR = 288


def bls12_g2_add(evm: Evm) -> None:
    """
    The bls12_381 G2 point addition precompile.

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
    if len(data) != 512:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(GAS_BLS_G2_ADD))

    # OPERATION
    p1 = unpad_g2(data[:256])
    p2 = unpad_g2(data[256:512])

    try:
        raw = g2_add(p1, p2)
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g2(raw)


def bls12_g2_msm(evm: Evm) -> None:
    """
    The bls12_381 G2 multi-scalar multiplication precompile.
    Note: This uses the naive approach to multi-scalar multiplication
    which is not suitably optimized for production clients. Clients are
    required to implement a more efficient algorithm such as the Pippenger
    algorithm.

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
    if len(data) == 0 or len(data) % LENGTH_PER_PAIR != 0:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    k = len(data) // LENGTH_PER_PAIR
    if k <= 128:
        discount = Uint(G2_K_DISCOUNT[k - 1])
    else:
        discount = Uint(G2_MAX_DISCOUNT)

    gas_cost = Uint(k) * GAS_BLS_G2_MUL * discount // MULTIPLIER
    charge_gas(evm, gas_cost)

    # OPERATION
    points = []
    scalars = []
    for i in range(k):
        start = i * LENGTH_PER_PAIR
        points.append(unpad_g2(data[start : start + 256]))
        scalars.append(bytes(buffer_read(data, U256(start + 256), U256(32))))

    try:
        raw = g2_msm(points, scalars)
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g2(raw)


def bls12_map_fp2_to_g2(evm: Evm) -> None:
    """
    Precompile to map field element to G2.

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
    if len(data) != 128:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(GAS_BLS_G2_MAP))

    # OPERATION
    fp2 = bytes(unpad_fp(data[:64]) + unpad_fp(data[64:]))

    try:
        raw = map_fp2_to_g2(fp2)
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g2(raw)
