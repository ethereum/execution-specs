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
from ...vm.error import OutOfGasError
from ...vm.gas import subtract_gas

GQUADDIVISOR = 20


def modexp(evm: Evm) -> None:
    """
    Calculates `(base ** exp) % modulus` for arbitary sized `base`, `exp` and.
    `modulus`. The return value is the same length as the modulus.
    """
    data = evm.message.data
    base_length = U256.from_be_bytes(data[0:32].ljust(32, b"\x00"))
    exp_length = U256.from_be_bytes(data[32:64].ljust(32, b"\x00"))
    modulus_length = U256.from_be_bytes(data[64:96].ljust(32, b"\x00"))

    if base_length == 0 and modulus_length == 0:
        evm.output = Bytes()
        return

    mult_complexity = get_mult_complexity(
        Uint(max(base_length, modulus_length))
    )
    # This is an estimate of the bit length of exp
    adjusted_exp_length = Uint(8 * max(0, int(exp_length) - 32))

    if (
        evm.gas_left
        < mult_complexity * max(1, adjusted_exp_length) // GQUADDIVISOR
    ):
        # This check must be done now to prevent loading of absurdly long
        # arguments. It is an underestimate, because adjusted_exp_length may
        # increase later.
        raise OutOfGasError()

    pointer = 96
    base_data = data[pointer : pointer + base_length].ljust(
        base_length, b"\x00"
    )
    base = Uint.from_be_bytes(base_data)
    pointer += base_length
    exp_data = data[pointer : pointer + exp_length].ljust(exp_length, b"\x00")
    exp = Uint.from_be_bytes(exp_data)
    pointer += exp_length
    modulus_data = data[pointer : pointer + modulus_length].ljust(
        modulus_length, b"\x00"
    )
    modulus = Uint.from_be_bytes(modulus_data)

    adjusted_exp_length = Uint(
        max(adjusted_exp_length, int(exp.bit_length()) - 1)
    )
    gas_used = mult_complexity * max(1, adjusted_exp_length) // GQUADDIVISOR

    # NOTE: It is in principle possible for the conversion to U256 to overflow
    # here. However, for this to happen without triggering the earlier check
    # would require providing more than 2**250 gas, which is obviously
    # not realistic.
    subtract_gas(evm, U256(gas_used))
    if modulus == 0:
        evm.output = Bytes(b"\x00") * modulus_length
    else:
        evm.output = Uint(pow(base, exp, modulus)).to_bytes(
            modulus_length, "big"
        )


def get_mult_complexity(x: Uint) -> Uint:
    """
    Estimate the complexity of performing Karatsuba multiplication.
    """
    if x <= 64:
        return x**2
    elif x <= 1024:
        return x**2 // 4 + 96 * x - 3072
    else:
        return x**2 // 16 + 480 * x - 199680
