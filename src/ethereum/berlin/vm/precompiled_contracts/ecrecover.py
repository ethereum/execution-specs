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
from ethereum.utils.byte import left_pad_zero_bytes, right_pad_zero_bytes

from ...vm import Evm
from ...vm.gas import GAS_ECRECOVER, subtract_gas


def ecrecover(evm: Evm) -> None:
    """
    Decrypts the address using elliptic curve DSA recovery mechanism and writes
    the address to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_ECRECOVER)
    data = right_pad_zero_bytes(evm.message.data, 128)
    message_hash_bytes = data[:32]
    message_hash = Hash32(message_hash_bytes)
    v_bytes = data[32:64]
    v = U256.from_be_bytes(v_bytes)
    r_bytes = data[64:96]
    r = U256.from_be_bytes(r_bytes)
    s_bytes = data[96:128]
    s = U256.from_be_bytes(s_bytes)

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
