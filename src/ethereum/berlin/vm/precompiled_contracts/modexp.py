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
from ethereum.utils.byte import right_pad_zero_bytes

from ...vm import Evm
from ...vm.gas import subtract_gas

GQUADDIVISOR = 3


def modexp(evm: Evm) -> None:
    """
    Calculates `(base**exp) % modulus` for arbitary sized `base`, `exp` and.
    `modulus`. The return value is the same length as the modulus.
    """
    data = evm.message.data
    base_length = U256.from_be_bytes(right_pad_zero_bytes(data[:32], 32))
    exp_length = U256.from_be_bytes(right_pad_zero_bytes(data[32:64], 32))
    modulus_length = U256.from_be_bytes(right_pad_zero_bytes(data[64:96], 32))

    exponent_head_start = 96 + base_length
    exponent_head_end = exponent_head_start + min(32, exp_length)

    exponent_head_bytes = data[exponent_head_start:exponent_head_end]
    exponent_head = Uint.from_be_bytes(exponent_head_bytes)

    gas_used = gas_cost(base_length, modulus_length, exp_length, exponent_head)

    if gas_used > U256.MAX_VALUE:
        gas_used = Uint(U256.MAX_VALUE)

    evm.gas_left = subtract_gas(evm.gas_left, U256(gas_used))

    if base_length == 0 and modulus_length == 0:
        evm.output = Bytes()
        return

    pointer = 96
    base_data = right_pad_zero_bytes(
        data[pointer : pointer + base_length], base_length
    )
    base = Uint.from_be_bytes(base_data)
    pointer += base_length
    exp_data = right_pad_zero_bytes(
        data[pointer : pointer + exp_length], exp_length
    )
    exp = Uint.from_be_bytes(exp_data)
    pointer += exp_length
    modulus_data = right_pad_zero_bytes(
        data[pointer : pointer + modulus_length], modulus_length
    )
    modulus = Uint.from_be_bytes(modulus_data)

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
