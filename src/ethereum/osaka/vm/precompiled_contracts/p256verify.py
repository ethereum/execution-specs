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

from ethereum.crypto.elliptic_curve import secp256r1_verify, SECP256R1N, SECP256R1P, SECP256R1A, SECP256R1B
from ethereum.crypto.hash import Hash32
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
    qx = U256.from_be_bytes(buffer_read(data, U256(96), U256(32)))
    qy = U256.from_be_bytes(buffer_read(data, U256(128), U256(32)))

    # Signature component bounds: Both r and s MUST satisfy 0 < r < n and 0 < s < n
    if not (U256(0) < r < SECP256R1N and U256(0) < s < SECP256R1N):
        return
    
    # Public key bounds: Both qx and qy MUST satisfy 0 ≤ qx < p and 0 ≤ qy < p
    if not (U256(0) <= qx < SECP256R1P and U256(0) <= qy < SECP256R1P):
        return

    # Point validity: The point (qx, qy) MUST satisfy the curve equation qy^2 ≡ qx^3 + a*qx + b (mod p)
    # Convert U256 to int for calculations
    qx_int = int(qx)
    qy_int = int(qy)
    p_int = int(SECP256R1P)
    a_int = int(SECP256R1A)
    b_int = int(SECP256R1B)

    # Calculate y^2 mod p
    y_squared = (qy_int * qy_int) % p_int
    
    # Calculate x^3 + ax + b mod p
    x_cubed = (qx_int * qx_int * qx_int) % p_int
    ax = (a_int * qx_int) % p_int
    right_side = (x_cubed + ax + b_int) % p_int

    if y_squared != right_side:
        return

    # Point not at infinity: The point (qx, qy) MUST NOT be the point at infinity (represented as (0, 0))
    if qx == U256(0) and qy == U256(0):
        return
    
    success_return_value = left_pad_zero_bytes(b"\x01", 32)
    
    try:
        secp256r1_verify(r, s, qx, qy, message_hash)
    except Exception:
        return

    evm.output = success_return_value

