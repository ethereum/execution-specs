"""
Ethereum Virtual Machine (EVM) MODEXP PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `MODEXP` precompiled contract.
"""
from ethereum.base_types import U256, Bytes, Uint

from ...vm import Evm
from ...vm.gas import charge_gas
from ..memory import buffer_read

GQUADDIVISOR = 3


def modexp(evm: Evm) -> None:
    """
    Calculates `(base**exp) % modulus` for arbitary sized `base`, `exp` and.
    `modulus`. The return value is the same length as the modulus.
    """
    data = evm.message.data

    # GAS
    base_length = U256.from_be_bytes(buffer_read(data, U256(0), U256(32)))
    exp_length = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    modulus_length = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))

    exp_start = U256(96) + base_length
    modulus_start = exp_start + exp_length

    exp_head = Uint.from_be_bytes(
        buffer_read(data, exp_start, min(U256(32), exp_length))
    )

    charge_gas(
        evm,
        gas_cost(base_length, modulus_length, exp_length, exp_head),
    )

    # OPERATION
    if base_length == 0 and modulus_length == 0:
        evm.output = Bytes()
        return

    base = Uint.from_be_bytes(buffer_read(data, U256(96), base_length))
    exp = Uint.from_be_bytes(buffer_read(data, exp_start, exp_length))
    modulus = Uint.from_be_bytes(
        buffer_read(data, modulus_start, modulus_length)
    )

    if modulus == 0:
        evm.output = Bytes(b"\x00") * modulus_length
    else:
        evm.output = Uint(pow(base, exp, modulus)).to_bytes(
            modulus_length, "big"
        )


def complexity(base_length: U256, modulus_length: U256) -> Uint:
    """
    Estimate the complexity of performing a modular exponentiation.

    Parameters
    ----------

    base_length :
        Length of the array representing the base integer.

    modulus_length :
        Length of the array representing the modulus integer.

    Returns
    -------

    complexity : `Uint`
        Complexity of performing the operation.
    """
    max_length = max(Uint(base_length), Uint(modulus_length))
    words = (max_length + 7) // 8
    return words**2


def iterations(exponent_length: U256, exponent_head: Uint) -> Uint:
    """
    Calculate the number of iterations required to perform a modular
    exponentiation.

    Parameters
    ----------

    exponent_length :
        Length of the array representing the exponent integer.

    exponent_head :
        First 32 bytes of the exponent (with leading zero padding if it is
        shorter than 32 bytes), as an unsigned integer.

    Returns
    -------

    iterations : `Uint`
        Number of iterations.
    """
    if exponent_length <= 32 and exponent_head == 0:
        count = Uint(0)
    elif exponent_length <= 32:
        bit_length = Uint(exponent_head.bit_length())

        if bit_length > 0:
            bit_length -= 1

        count = bit_length
    else:
        length_part = 8 * (Uint(exponent_length) - 32)
        bits_part = Uint(exponent_head.bit_length())

        if bits_part > 0:
            bits_part -= 1

        count = length_part + bits_part

    return max(count, Uint(1))


def gas_cost(
    base_length: U256,
    modulus_length: U256,
    exponent_length: U256,
    exponent_head: Uint,
) -> Uint:
    """
    Calculate the gas cost of performing a modular exponentiation.

    Parameters
    ----------

    base_length :
        Length of the array representing the base integer.

    modulus_length :
        Length of the array representing the modulus integer.

    exponent_length :
        Length of the array representing the exponent integer.

    exponent_head :
        First 32 bytes of the exponent (with leading zero padding if it is
        shorter than 32 bytes), as an unsigned integer.

    Returns
    -------

    gas_cost : `Uint`
        Gas required for performing the operation.
    """
    multiplication_complexity = complexity(base_length, modulus_length)
    iteration_count = iterations(exponent_length, exponent_head)
    cost = multiplication_complexity * iteration_count
    cost //= GQUADDIVISOR
    return max(Uint(200), cost)
