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
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ...vm import Evm
from ...vm.exceptions import ExceptionalHalt
from ...vm.gas import charge_gas
from ..memory import buffer_read


def modexp(evm: Evm) -> None:
    """
    Calculates `(base**exp) % modulus` for arbitrary sized `base`, `exp` and.
    `modulus`. The return value is the same length as the modulus.
    """
    data = evm.message.data

    # GAS
    base_length = U256.from_be_bytes(buffer_read(data, U256(0), U256(32)))
    if base_length > U256(1024):
        raise ExceptionalHalt("Mod-exp base length is too large")

    exp_length = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    if exp_length > U256(1024):
        raise ExceptionalHalt("Mod-exp exponent length is too large")

    modulus_length = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))
    if modulus_length > U256(1024):
        raise ExceptionalHalt("Mod-exp modulus length is too large")

    exp_start = U256(96) + base_length

    exp_head = U256.from_be_bytes(
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

    modulus_start = exp_start + exp_length
    modulus = Uint.from_be_bytes(
        buffer_read(data, modulus_start, modulus_length)
    )

    if modulus == 0:
        evm.output = Bytes(b"\x00") * modulus_length
    else:
        evm.output = pow(base, exp, modulus).to_bytes(
            Uint(modulus_length), "big"
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
    words = (max_length + Uint(7)) // Uint(8)
    complexity = Uint(16)
    if max_length > Uint(32):
        complexity = Uint(2) * words ** Uint(2)
    return complexity


def iterations(exponent_length: U256, exponent_head: U256) -> Uint:
    """
    Calculate the number of iterations required to perform a modular
    exponentiation.

    Parameters
    ----------

    exponent_length :
        Length of the array representing the exponent integer.

    exponent_head :
        First 32 bytes of the exponent (with leading zero padding if it is
        shorter than 32 bytes), as a U256.

    Returns
    -------

    iterations : `Uint`
        Number of iterations.
    """
    if exponent_length <= U256(32) and exponent_head == U256(0):
        count = Uint(0)
    elif exponent_length <= U256(32):
        bit_length = exponent_head.bit_length()

        if bit_length > Uint(0):
            bit_length -= Uint(1)

        count = bit_length
    else:
        length_part = Uint(16) * (Uint(exponent_length) - Uint(32))
        bits_part = exponent_head.bit_length()

        if bits_part > Uint(0):
            bits_part -= Uint(1)

        count = length_part + bits_part

    return max(count, Uint(1))


def gas_cost(
    base_length: U256,
    modulus_length: U256,
    exponent_length: U256,
    exponent_head: U256,
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
        shorter than 32 bytes), as a U256.

    Returns
    -------

    gas_cost : `Uint`
        Gas required for performing the operation.
    """
    multiplication_complexity = complexity(base_length, modulus_length)
    iteration_count = iterations(exponent_length, exponent_head)
    cost = multiplication_complexity * iteration_count
    return max(Uint(500), cost)
