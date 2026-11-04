"""
Ethereum Virtual Machine (EVM) SPHINCS_VERIFY PRECOMPILED CONTRACT.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `SPHINCS_VERIFY` precompiled contract.
"""

from ethereum_types.bytes import Bytes32

from ethereum.crypto.sphincs import (
    SPHINCS_MESSAGE_LENGTH,
    SPHINCS_PUBLIC_KEY_LENGTH,
    SPHINCS_SIGNATURE_LENGTH,
)
from ethereum.crypto.sphincs import sphincs_verify as verify
from ethereum.utils.byte import left_pad_zero_bytes

from ...vm import Evm
from ...vm.gas import GasCosts, charge_gas

SPHINCS_VERIFY_INPUT_LENGTH = (
    SPHINCS_MESSAGE_LENGTH
    + SPHINCS_PUBLIC_KEY_LENGTH
    + SPHINCS_SIGNATURE_LENGTH
)
"""
Exact input length: the message, the public key, then the signature.
"""


def sphincs_verify(evm: Evm) -> None:
    """
    Verify a leanSPHINCS signature.

    The input is a 32-byte message, a 32-byte public key and a
    7740-byte signature. The output is `1` as a 32-byte word when the
    signature signs the message under the public key, and empty
    otherwise, including for an input of any other length.
    """
    data = evm.call_data

    # GAS
    charge_gas(evm, GasCosts.PRECOMPILE_SPHINCS_VERIFY)

    if len(data) != SPHINCS_VERIFY_INPUT_LENGTH:
        return

    # OPERATION
    message_end = SPHINCS_MESSAGE_LENGTH
    public_key_end = message_end + SPHINCS_PUBLIC_KEY_LENGTH
    message = Bytes32(data[:message_end])
    public_key = data[message_end:public_key_end]
    signature = data[public_key_end:]

    if not verify(public_key, message, signature):
        return

    evm.output = left_pad_zero_bytes(b"\x01", 32)
