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
from eth2spec.deneb.mainnet import (
    KZGCommitment,
    kzg_commitment_to_versioned_hash,
    verify_kzg_proof,
)

from ethereum.base_types import U256, Bytes
from ethereum.utils.ensure import ensure

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

    ensure(len(data) == 192, KZGProofError)

    versioned_hash = data[:32]
    z = data[32:64]
    y = data[64:96]
    commitment = KZGCommitment(data[96:144])
    proof = data[144:192]

    # GAS
    charge_gas(evm, GAS_POINT_EVALUATION)

    # OPERATION
    # Verify commitment matches versioned_hash
    ensure(
        kzg_commitment_to_versioned_hash(commitment) == versioned_hash,
        KZGProofError,
    )

    # Verify KZG proof with z and y in big endian format
    try:
        kzg_proof_verification = verify_kzg_proof(commitment, z, y, proof)
    except Exception as e:
        raise KZGProofError from e

    ensure(kzg_proof_verification, KZGProofError)

    # Return FIELD_ELEMENTS_PER_BLOB and BLS_MODULUS as padded
    # 32 byte big endian values
    evm.output = Bytes(
        U256(FIELD_ELEMENTS_PER_BLOB).to_be_bytes32()
        + U256(BLS_MODULUS).to_be_bytes32()
    )
