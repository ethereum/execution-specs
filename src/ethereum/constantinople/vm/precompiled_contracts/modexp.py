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

GQUADDIVISOR = Uint(20)


def modexp(evm: Evm) -> None:
    """
    Calculates `(base**exp) % modulus` for arbitrary sized `base`, `exp` and.
    `modulus`. The return value is the same length as the modulus.
    """
    data = evm.message.data

    # GAS
    base_length = U256.from_be_bytes(buffer_read(data, U256(0), U256(32)))
    exp_length = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    modulus_length = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))

    exp_start = U256(96) + base_length

    exp_head = U256.from_be_bytes(
        buffer_read(data, exp_start, min(U256(32), exp_length))
    )
    if exp_length < 32:
        adjusted_exp_length = Uint(max(0, exp_head.bit_length() - 1))
    else:
        adjusted_exp_length = Uint(
            8 * (int(exp_length) - 32) + max(0, exp_head.bit_length() - 1)
        )

    charge_gas(
        evm,
        (
            get_mult_complexity(Uint(max(base_length, modulus_length)))
            * max(adjusted_exp_length, Uint(1))
        )
        // GQUADDIVISOR,
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
