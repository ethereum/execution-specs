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
from py_ecc.bls12_381.bls12_381_curve import add, multiply
from py_ecc.bls.hash_to_curve import clear_cofactor_G1, map_to_curve_G1
from py_ecc.optimized_bls12_381.optimized_curve import FQ as OPTIMIZED_FQ
from py_ecc.optimized_bls12_381.optimized_curve import normalize

from ethereum.base_types import U256, Uint

from ....vm import Evm
from ....vm.gas import (
    GAS_BLS_G1_ADD,
    GAS_BLS_G1_MAP,
    GAS_BLS_G1_MUL,
    charge_gas,
)
from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter
from . import (
    G1_K_DISCOUNT,
    G1_MAX_DISCOUNT,
    MULTIPLIER,
    G1_to_bytes,
    bytes_to_FQ,
    bytes_to_G1,
    decode_G1_scalar_pair,
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
    charge_gas(evm, Uint(GAS_BLS_G1_ADD))

    # OPERATION
    p1 = bytes_to_G1(buffer_read(data, U256(0), U256(128)))
    p2 = bytes_to_G1(buffer_read(data, U256(128), U256(128)))

    result = add(p1, p2)

    evm.output = G1_to_bytes(result)


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
        discount = G1_K_DISCOUNT[k - 1]
    else:
        discount = G1_MAX_DISCOUNT

    gas_cost = Uint(k * GAS_BLS_G1_MUL * discount // MULTIPLIER)
    charge_gas(evm, gas_cost)

    # OPERATION
    for i in range(k):
        start_index = i * LENGTH_PER_PAIR
        end_index = start_index + LENGTH_PER_PAIR

        p, m = decode_G1_scalar_pair(data[start_index:end_index])
        product = multiply(p, m)

        if i == 0:
            result = product
        else:
            result = add(result, product)

    evm.output = G1_to_bytes(result)


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
    charge_gas(evm, Uint(GAS_BLS_G1_MAP))

    # OPERATION
    field_element = bytes_to_FQ(data, True)
    assert isinstance(field_element, OPTIMIZED_FQ)

    g1_uncompressed = clear_cofactor_G1(map_to_curve_G1(field_element))
    g1_normalised = normalize(g1_uncompressed)

    evm.output = G1_to_bytes(g1_normalised)
