"""
Ethereum Virtual Machine (EVM) IDENTITY PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `IDENTITY` precompiled contract.
"""
from ethereum.base_types import U256
from ethereum.crypto.alt_bn128 import BNF, BNP, alt_bn128_prime

from ...vm import Evm
from ...vm.error import OutOfGasError
from ...vm.gas import subtract_gas


def alt_bn128_add(evm: Evm) -> None:
    """
    Writes the message data to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    x0_bytes = evm.message.data[0:32].ljust(32, b"\x00")
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = evm.message.data[32:64].ljust(32, b"\x00")
    y0_value = U256.from_be_bytes(y0_bytes)
    x1_bytes = evm.message.data[64:96].ljust(32, b"\x00")
    x1_value = U256.from_be_bytes(x1_bytes)
    y1_bytes = evm.message.data[96:128].ljust(32, b"\x00")
    y1_value = U256.from_be_bytes(y1_bytes)

    for i in (x0_value, y0_value, x1_value, y1_value):
        if i >= alt_bn128_prime:
            raise OutOfGasError

    try:
        p0 = BNP(BNF(x0_value), BNF(y0_value))
        p1 = BNP(BNF(x1_value), BNF(y1_value))
    except ValueError:
        raise OutOfGasError

    p = p0 + p1

    evm.gas_left = subtract_gas(evm.gas_left, U256(500))
    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()


def alt_bn128_mul(evm: Evm) -> None:
    """
    Writes the message data to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    x0_bytes = evm.message.data[0:32].ljust(32, b"\x00")
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = evm.message.data[32:64].ljust(32, b"\x00")
    y0_value = U256.from_be_bytes(y0_bytes)
    n = U256.from_be_bytes(evm.message.data[64:96].ljust(32, b"\x00"))

    for i in (x0_value, y0_value):
        if i >= alt_bn128_prime:
            raise OutOfGasError

    try:
        p0 = BNP(BNF(x0_value), BNF(y0_value))
    except ValueError:
        raise OutOfGasError

    p = p0.mul_by(n)

    evm.gas_left = subtract_gas(evm.gas_left, U256(40000))
    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()
