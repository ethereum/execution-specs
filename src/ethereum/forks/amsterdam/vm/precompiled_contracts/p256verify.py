"""
Ethereum Virtual Machine (EVM) P256VERIFY PRECOMPILED CONTRACT.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction.
------------
Implementation of the P256VERIFY precompiled contract.
"""

from ethereum_types.numeric import U256

from ethereum.crypto.elliptic_curve import (
    SECP256R1N,
    SECP256R1P,
    is_on_curve_secp256r1,
    secp256r1_verify,
)
from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidSignatureError
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

    if len(data) != 160:
        return

    # OPERATION
    message_hash_bytes = buffer_read(data, U256(0), U256(32))
    message_hash = Hash32(message_hash_bytes)
    r = U256.from_be_bytes(buffer_read(data, U256(32), U256(32)))
    s = U256.from_be_bytes(buffer_read(data, U256(64), U256(32)))
    public_key_x = U256.from_be_bytes(
        buffer_read(data, U256(96), U256(32))
    )  # qx
    public_key_y = U256.from_be_bytes(
        buffer_read(data, U256(128), U256(32))
    )  # qy

    # Signature component bounds:
    # Both r and s MUST satisfy 0 < r < n and 0 < s < n
    if r <= U256(0) or r >= SECP256R1N:
        return
    if s <= U256(0) or s >= SECP256R1N:
        return

    # Public key bounds:
    # Both qx and qy MUST satisfy 0 ≤ qx < p and 0 ≤ qy < p
    # U256 is unsigned, so we don't need to check for < 0
    if public_key_x >= SECP256R1P:
        return
    if public_key_y >= SECP256R1P:
        return

    # Point should not be at infinity (represented as (0, 0))
    if public_key_x == U256(0) and public_key_y == U256(0):
        return

    # Point validity: The point (qx, qy) MUST satisfy the curve equation
    # qy^2 ≡ qx^3 + a*qx + b (mod p)
    if not is_on_curve_secp256r1(public_key_x, public_key_y):
        return

    try:
        secp256r1_verify(r, s, public_key_x, public_key_y, message_hash)
    except InvalidSignatureError:
        return

    evm.output = left_pad_zero_bytes(b"\x01", 32)
