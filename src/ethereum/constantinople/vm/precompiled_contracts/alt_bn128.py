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
from ethereum.base_types import U256
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
from ethereum.utils.byte import right_pad_zero_bytes
from ethereum.utils.ensure import ensure

from ...vm import Evm
from ...vm.error import OutOfGasError
from ...vm.gas import subtract_gas


def alt_bn128_add(evm: Evm) -> None:
    """
    The ALT_BN128 addition precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    x0_bytes = right_pad_zero_bytes(evm.message.data[:32], 32)
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = right_pad_zero_bytes(evm.message.data[32:64], 32)
    y0_value = U256.from_be_bytes(y0_bytes)
    x1_bytes = right_pad_zero_bytes(evm.message.data[64:96], 32)
    x1_value = U256.from_be_bytes(x1_bytes)
    y1_bytes = right_pad_zero_bytes(evm.message.data[96:128], 32)
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

    evm.gas_left = subtract_gas(evm.gas_left, U256(500))
    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()


def alt_bn128_mul(evm: Evm) -> None:
    """
    The ALT_BN128 multiplication precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    x0_bytes = right_pad_zero_bytes(evm.message.data[:32], 32)
    x0_value = U256.from_be_bytes(x0_bytes)
    y0_bytes = right_pad_zero_bytes(evm.message.data[32:64], 32)
    y0_value = U256.from_be_bytes(y0_bytes)
    n = U256.from_be_bytes(right_pad_zero_bytes(evm.message.data[64:96], 32))

    for i in (x0_value, y0_value):
        if i >= ALT_BN128_PRIME:
            raise OutOfGasError

    try:
        p0 = BNP(BNF(x0_value), BNF(y0_value))
    except ValueError:
        raise OutOfGasError

    p = p0.mul_by(n)

    evm.gas_left = subtract_gas(evm.gas_left, U256(40000))
    evm.output = p.x.to_be_bytes32() + p.y.to_be_bytes32()


def alt_bn128_pairing_check(evm: Evm) -> None:
    """
    The ALT_BN128 pairing check precompiled contract.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    if len(evm.message.data) % 192 != 0:
        raise OutOfGasError
    evm.gas_left = subtract_gas(
        evm.gas_left, U256(80000 * (len(evm.message.data) // 192) + 100000)
    )
    result = BNF12.from_int(1)
    for i in range(len(evm.message.data) // 192):
        values = []
        for j in range(6):
            value = U256.from_be_bytes(
                evm.message.data[i * 192 + 32 * j : i * 192 + 32 * (j + 1)]
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
