"""
Ethereum Virtual Machine (EVM) POINT EVALUATION PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the POINT EVALUATION precompiled contract.
"""
from ethereum_types.bytes import Bytes, Bytes32, Bytes48
from ethereum_types.numeric import U256

from ethereum.crypto.kzg import (
    KZGCommitment,
    kzg_commitment_to_versioned_hash,
    verify_kzg_proof,
)

from ...vm import Evm
from ...vm.exceptions import KZGProofError
from ...vm.gas import GAS_POINT_EVALUATION, charge_gas

FIELD_ELEMENTS_PER_BLOB = 4096
BLS_MODULUS = 52435875175126190479447740508185965837690552500527637822603658699938581184513  # noqa: E501
VERSIONED_HASH_VERSION_KZG = b"\x01"


def point_evaluation(evm: Evm) -> None:
    """
    A pre-compile that verifies a KZG proof which claims that a blob
    (represented by a commitment) evaluates to a given value at a given point.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    data = evm.message.data
    if len(data) != 192:
        raise KZGProofError

    versioned_hash = data[:32]
    z = Bytes32(data[32:64])
    y = Bytes32(data[64:96])
    commitment = KZGCommitment(data[96:144])
    proof = Bytes48(data[144:192])

    # GAS
    charge_gas(evm, GAS_POINT_EVALUATION)
    if kzg_commitment_to_versioned_hash(commitment) != versioned_hash:
        raise KZGProofError

    # Verify KZG proof with z and y in big endian format
    try:
        kzg_proof_verification = verify_kzg_proof(commitment, z, y, proof)
    except Exception as e:
        raise KZGProofError from e

    if not kzg_proof_verification:
        raise KZGProofError

    # Return FIELD_ELEMENTS_PER_BLOB and BLS_MODULUS as padded
    # 32 byte big endian values
    evm.output = Bytes(
        U256(FIELD_ELEMENTS_PER_BLOB).to_be_bytes32()
        + U256(BLS_MODULUS).to_be_bytes32()
    )
