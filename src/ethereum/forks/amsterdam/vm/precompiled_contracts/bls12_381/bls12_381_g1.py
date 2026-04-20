"""
Ethereum Virtual Machine (EVM) BLS12 381 CONTRACTS.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of pre-compiles in G1 (curve over base prime field).
"""

from ethereum_types.numeric import U256, Uint

from ethereum.crypto.bls12_381 import g1_add, g1_msm, map_fp_to_g1

from ....vm import Evm
from ....vm.gas import (
    GAS_PRECOMPILE_BLS_G1ADD,
    GAS_PRECOMPILE_BLS_G1MAP,
    GAS_PRECOMPILE_BLS_G1MUL,
    charge_gas,
)
from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter
from . import (
    G1_K_DISCOUNT,
    G1_MAX_DISCOUNT,
    MULTIPLIER,
    pad_g1,
    unpad_fp,
    unpad_g1,
)

LENGTH_PER_PAIR = 160


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
    charge_gas(evm, Uint(GAS_PRECOMPILE_BLS_G1ADD))

    # OPERATION
    p1 = unpad_g1(data[:128])
    p2 = unpad_g1(data[128:256])

    try:
        raw = g1_add(p1, p2)
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g1(raw)


def bls12_g1_msm(evm: Evm) -> None:
    """
    The bls12_381 G1 multi-scalar multiplication precompile.
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
        discount = Uint(G1_K_DISCOUNT[k - 1])
    else:
        discount = Uint(G1_MAX_DISCOUNT)

    gas_cost = Uint(k) * GAS_PRECOMPILE_BLS_G1MUL * discount // MULTIPLIER
    charge_gas(evm, gas_cost)

    # OPERATION
    points = []
    scalars = []
    for i in range(k):
        start = i * LENGTH_PER_PAIR
        points.append(unpad_g1(data[start : start + 128]))
        scalars.append(bytes(buffer_read(data, U256(start + 128), U256(32))))

    try:
        raw = g1_msm(points, scalars)
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g1(raw)


def bls12_map_fp_to_g1(evm: Evm) -> None:
    """
    Precompile to map field element to G1.

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
    if len(data) != 64:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(GAS_PRECOMPILE_BLS_G1MAP))

    # OPERATION
    fp = unpad_fp(data)

    try:
        raw = map_fp_to_g1(bytes(fp))
    except ValueError as e:
        raise InvalidParameter(str(e)) from e

    evm.output = pad_g1(raw)
