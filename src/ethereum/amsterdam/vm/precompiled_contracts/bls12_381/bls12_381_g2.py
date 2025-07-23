"""
Ethereum Virtual Machine (EVM) BLS12 381 G2 CONTRACTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of pre-compiles in G2 (curve over base prime field).
"""

from ethereum_types.numeric import U256, Uint
from py_ecc.bls.hash_to_curve import clear_cofactor_G2, map_to_curve_G2
from py_ecc.optimized_bls12_381.optimized_curve import FQ2
from py_ecc.optimized_bls12_381.optimized_curve import add as bls12_add
from py_ecc.optimized_bls12_381.optimized_curve import (
    multiply as bls12_multiply,
)

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
    bytes_to_fq2,
    bytes_to_g2,
    decode_g2_scalar_pair,
    g2_to_bytes,
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
    p1 = bytes_to_g2(buffer_read(data, U256(0), U256(256)))
    p2 = bytes_to_g2(buffer_read(data, U256(256), U256(256)))

    result = bls12_add(p1, p2)

    evm.output = g2_to_bytes(result)


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
    for i in range(k):
        start_index = i * LENGTH_PER_PAIR
        end_index = start_index + LENGTH_PER_PAIR

        p, m = decode_g2_scalar_pair(data[start_index:end_index])
        product = bls12_multiply(p, m)

        if i == 0:
            result = product
        else:
            result = bls12_add(result, product)

    evm.output = g2_to_bytes(result)


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
    field_element = bytes_to_fq2(data)
    assert isinstance(field_element, FQ2)

    fp2 = bytes_to_fq2(data)
    g2_3d = clear_cofactor_G2(map_to_curve_G2(fp2))

    evm.output = g2_to_bytes(g2_3d)
