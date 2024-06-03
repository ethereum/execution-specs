"""
Ethereum Virtual Machine (EVM) ALT_BN128 CONTRACTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the ALT_BN128 precompiled contracts.
"""
from ethereum.base_types import U256, Uint
from ethereum.crypto.alt_bn128 import (
    ALT_BN128_CURVE_ORDER,
    ALT_BN128_PRIME,
    BNF,
    BNF2,
    BNF12,
    BNP,
    BNP2,
    pairing,
)
from ethereum.utils.ensure import ensure

from ...vm import Evm
from ...vm.gas import charge_gas
from ...vm.memory import buffer_read
from ..exceptions import OutOfGasError


def alt_bn128_add(evm: Evm) -> None:
    """
    The ALT_BN128 addition precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(150))

    # OPERATION
    x0_bytes = buffer_read(data, U256(0), U256(32))
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = buffer_read(data, U256(32), U256(32))
    y0_value = U256.from_be_bytes(y0_bytes)
    x1_bytes = buffer_read(data, U256(64), U256(32))
    x1_value = U256.from_be_bytes(x1_bytes)
    y1_bytes = buffer_read(data, U256(96), U256(32))
    y1_value = U256.from_be_bytes(y1_bytes)

    for i in (x0_value, y0_value, x1_value, y1_value):
        if i >= ALT_BN128_PRIME:
            raise OutOfGasError

    try:
        p0 = BNP(BNF(x0_value), BNF(y0_value))
        p1 = BNP(BNF(x1_value), BNF(y1_value))
    except ValueError:
        raise OutOfGasError

    p = p0 + p1

    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()


def alt_bn128_mul(evm: Evm) -> None:
    """
    The ALT_BN128 multiplication precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(6000))

    # OPERATION
    x0_bytes = buffer_read(data, U256(0), U256(32))
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = buffer_read(data, U256(32), U256(32))
    y0_value = U256.from_be_bytes(y0_bytes)
    n = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))

    for i in (x0_value, y0_value):
        if i >= ALT_BN128_PRIME:
            raise OutOfGasError

    try:
        p0 = BNP(BNF(x0_value), BNF(y0_value))
    except ValueError:
        raise OutOfGasError

    p = p0.mul_by(n)

    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()


def alt_bn128_pairing_check(evm: Evm) -> None:
    """
    The ALT_BN128 pairing check precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    charge_gas(evm, Uint(34000 * (len(data) // 192) + 45000))

    # OPERATION
    if len(data) % 192 != 0:
        raise OutOfGasError
    result = BNF12.from_int(1)
    for i in range(len(data) // 192):
        values = []
        for j in range(6):
            value = U256.from_be_bytes(
                data[i * 192 + 32 * j : i * 192 + 32 * (j + 1)]
            )
            if value >= ALT_BN128_PRIME:
                raise OutOfGasError
            values.append(int(value))

        try:
            p = BNP(BNF(values[0]), BNF(values[1]))
            q = BNP2(
                BNF2((values[3], values[2])), BNF2((values[5], values[4]))
            )
        except ValueError:
            raise OutOfGasError()
        ensure(
            p.mul_by(ALT_BN128_CURVE_ORDER) == BNP.point_at_infinity(),
            OutOfGasError,
        )
        ensure(
            q.mul_by(ALT_BN128_CURVE_ORDER) == BNP2.point_at_infinity(),
            OutOfGasError,
        )
        if p != BNP.point_at_infinity() and q != BNP2.point_at_infinity():
            result = result * pairing(q, p)

    if result == BNF12.from_int(1):
        evm.output = U256(1).to_be_bytes32()
    else:
        evm.output = U256(0).to_be_bytes32()
