"""
Ethereum Virtual Machine (EVM) Sigrecover PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `Sigrecover` precompiled contract.
"""
from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U8, U256, Uint

from ...signature_algorithms import algorithm_from_type
from ...vm import Evm
from ...vm.gas import GAS_SIGRECOVER, charge_gas
from ..exceptions import InvalidParameter
from ...exceptions import InvalidAlgorithm
from ..gas import GAS_PER_ADDITIONAL_AUTH_BYTE

NULL_ADDRESS = Bytes20.fromhex("0000000000000000000000000000000000000000")


def sigrecover(evm: Evm) -> None:
    """
    Recovers the EIP-7932 signature and writes the address to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    charge_gas(evm, GAS_SIGRECOVER)

    data = evm.message.data

    if len(data) < 64:
        raise InvalidParameter

    hash = Bytes32(data[:32])
    alg_type = U8(data[32])
    signature_length = U256(int.from_bytes(data[33:64], "little"))

    if alg_type == U8(0xFF):
        evm.output = NULL_ADDRESS
        return

    try:
        alg = algorithm_from_type(alg_type)
    except InvalidAlgorithm:
        evm.output = NULL_ADDRESS
        return

    if signature_length > U256(alg.max_length) or signature_length != U256(
        len(data) - 64
    ):
        evm.output = NULL_ADDRESS
        return

    charge_gas(
        evm,
        (
            Uint(max(0, int(signature_length) - 65))
            * GAS_PER_ADDITIONAL_AUTH_BYTE
        )
        + Uint(alg.gas_penalty),
    )

    evm.output = alg.verify(data[64 : 64 + int(signature_length)], hash)
