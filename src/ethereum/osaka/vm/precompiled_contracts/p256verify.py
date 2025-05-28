"""
Ethereum Virtual Machine (EVM) P256VERIFY PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the P256VERIFY precompiled contract.
"""
from ethereum_types.numeric import U256

from ethereum.crypto.elliptic_curve import secp256r1_verify
from ethereum.crypto.hash import Hash32
from cryptography.exceptions import InvalidSignature
from ethereum.utils.byte import left_pad_zero_bytes

from ...vm import Evm
from ...vm.gas import GAS_P256VERIFY, charge_gas
from ...vm.memory import buffer_read


def p256verify(evm: Evm) -> None:
    """
    Verifies a P-256 signature.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    charge_gas(evm, GAS_P256VERIFY)

    # OPERATION
    message_hash_bytes = buffer_read(data, U256(0), U256(32))
    message_hash = Hash32(message_hash_bytes)
    r = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    s = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))
    x = U256.from_be_bytes(buffer_read(data, U256(96), U256(32)))
    y = U256.from_be_bytes(buffer_read(data, U256(128), U256(32)))

    if x == U256(0) or y == U256(0):
        return
    
    success_return_value = left_pad_zero_bytes(b"\x01", 32)
    
    try:
        secp256r1_verify(r, s, x, y, message_hash)
    except InvalidSignature:
        return

    evm.output = success_return_value

