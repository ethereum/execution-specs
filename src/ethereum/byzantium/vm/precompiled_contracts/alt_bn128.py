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
from ethereum.crypto.alt_bn128 import (
    BNF,
    BNF2,
    BNF12,
    BNP,
    BNP2,
    alt_bn128_prime,
    alt_bn128_curve_order,
    pairing,
)
from ethereum.utils.ensure import ensure

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


def alt_bn128_pairing_check(evm: Evm) -> None:
    """F"""
    try:
        print("Doing Check")
        ensure(len(evm.message.data) % 192 == 0, OutOfGasError)
        print("Doing Check 2")
        evm.gas_left = subtract_gas(
            evm.gas_left, U256(80000 * (len(evm.message.data) // 192) + 100000)
        )
        result = BNF12.from_int(1)
        print("Doing Check 3")
        for i in range(len(evm.message.data) // 192):
            values = []
            for j in range(6):
                value = U256.from_be_bytes(
                    evm.message.data[i + 32 * j : i + 32 * (j + 1)]
                )
                if value >= alt_bn128_prime:
                    print(value)
                    ensure(value < alt_bn128_prime)
                values.append(int(value))

            try:
                p = BNP(BNF(values[0]), BNF(values[1]))
                q = BNP2(
                    BNF2((values[3], values[2])), BNF2((values[5], values[4]))
                )
            except ValueError:
                print("Invalid Point")
                raise OutOfGasError()
            ensure(p.mul_by(alt_bn128_curve_order) == BNP.inf(), OutOfGasError)
            ensure(q.mul_by(alt_bn128_curve_order) == BNP2.inf(), OutOfGasError)
            if p != BNP.inf() and q != BNP2.inf():
                result = result * pairing(q, p)

        if result == BNF12.from_int(1):
            print("Aye")
            evm.output = U256(1).to_be_bytes32()
        else:
            print("No")
            evm.output = U256(0).to_be_bytes32()
    except Exception:
        from traceback import print_exc

        print_exc()
        raise
