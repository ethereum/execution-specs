"""
Ethereum Virtual Machine (EVM) ECRECOVER PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the ECRECOVER precompiled contract.
"""
from ethereum.base_types import U256
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.byte import left_pad_zero_bytes

from ...vm import Evm
from ...vm.gas import GAS_ECRECOVER, charge_gas
from ...vm.memory import buffer_read


def ecrecover(evm: Evm) -> None:
    """
    Decrypts the address using elliptic curve DSA recovery mechanism and writes
    the address to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    data = evm.message.data

    # GAS
    charge_gas(evm, GAS_ECRECOVER)

    # OPERATION
    message_hash_bytes = buffer_read(data, U256(0), U256(32))
    message_hash = Hash32(message_hash_bytes)
    v = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    r = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))
    s = U256.from_be_bytes(buffer_read(data, U256(96), U256(32)))

    if v != 27 and v != 28:
        return
    if 0 >= r or r >= SECP256K1N:
        return
    if 0 >= s or s >= SECP256K1N:
        return

    try:
        public_key = secp256k1_recover(r, s, v - 27, message_hash)
    except ValueError:
        # unable to extract public key
        return

    address = keccak256(public_key)[12:32]
    padded_address = left_pad_zero_bytes(address, 32)
    evm.output = padded_address
