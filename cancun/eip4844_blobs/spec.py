"""Defines EIP-4844 specification constants and functions."""

import itertools
from dataclasses import dataclass
from hashlib import sha256
from typing import List, Optional, Tuple

from ethereum_test_forks import Fork
from ethereum_test_tools import Transaction


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_4844 = ReferenceSpec("EIPS/eip-4844.md", "f0eb6a364aaf5ccb43516fa2c269a54fb881ecfd")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-4844 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-4844#parameters.

    If the parameter is not currently used within the tests, it is commented
    out.
    """

    BLOB_TX_TYPE = 0x03
    FIELD_ELEMENTS_PER_BLOB = 4096
    BLS_MODULUS = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    BLOB_COMMITMENT_VERSION_KZG = 1
    POINT_EVALUATION_PRECOMPILE_ADDRESS = 10
    POINT_EVALUATION_PRECOMPILE_GAS = 50_000
    # MAX_VERSIONED_HASHES_LIST_SIZE = 2**24
    # MAX_CALLDATA_SIZE = 2**24
    # MAX_ACCESS_LIST_SIZE = 2**24
    # MAX_ACCESS_LIST_STORAGE_KEYS = 2**24
    # MAX_TX_WRAP_COMMITMENTS = 2**12
    # LIMIT_BLOBS_PER_TX = 2**12
    HASH_OPCODE_BYTE = 0x49
    HASH_GAS_COST = 3

    @classmethod
    def kzg_to_versioned_hash(
        cls,
        kzg_commitment: bytes | int,  # 48 bytes
        blob_commitment_version_kzg: Optional[bytes | int] = None,
    ) -> bytes:
        """Calculate versioned hash for a given KZG commitment."""
        if blob_commitment_version_kzg is None:
            blob_commitment_version_kzg = cls.BLOB_COMMITMENT_VERSION_KZG
        if isinstance(kzg_commitment, int):
            kzg_commitment = kzg_commitment.to_bytes(48, "big")
        if isinstance(blob_commitment_version_kzg, int):
            blob_commitment_version_kzg = blob_commitment_version_kzg.to_bytes(1, "big")
        return blob_commitment_version_kzg + sha256(kzg_commitment).digest()[1:]

    @classmethod
    def get_total_blob_gas(cls, *, tx: Transaction, blob_gas_per_blob: int) -> int:
        """Calculate the total blob gas for a transaction."""
        if tx.blob_versioned_hashes is None:
            return 0
        return blob_gas_per_blob * len(tx.blob_versioned_hashes)


@dataclass(frozen=True)
class SpecHelpers:
    """
    Define parameters and helper functions that are tightly coupled to the 4844
    spec but not strictly part of it.
    """

    BYTES_PER_FIELD_ELEMENT = 32

    @classmethod
    def get_min_excess_blob_gas_for_blob_gas_price(
        cls,
        *,
        fork: Fork,
        blob_gas_price: int,
    ) -> int:
        """
        Get the minimum required excess blob gas value to get a given blob gas cost in a
        block.
        """
        current_excess_blob_gas = 0
        current_blob_gas_price = 1
        get_blob_gas_price = fork.blob_gas_price_calculator()
        gas_per_blob = fork.blob_gas_per_blob()
        while current_blob_gas_price < blob_gas_price:
            current_excess_blob_gas += gas_per_blob
            current_blob_gas_price = get_blob_gas_price(excess_blob_gas=current_excess_blob_gas)
        return current_excess_blob_gas

    @classmethod
    def get_min_excess_blobs_for_blob_gas_price(
        cls,
        *,
        fork: Fork,
        blob_gas_price: int,
    ) -> int:
        """Get the minimum required excess blobs to get a given blob gas cost in a block."""
        gas_per_blob = fork.blob_gas_per_blob()
        return (
            cls.get_min_excess_blob_gas_for_blob_gas_price(
                fork=fork,
                blob_gas_price=blob_gas_price,
            )
            // gas_per_blob
        )

    @classmethod
    def get_blob_combinations(
        cls,
        blob_count: int,
    ) -> List[Tuple[int, ...]]:
        """Get all possible combinations of blobs that result in a given blob count."""
        combinations = [
            seq
            for i in range(
                blob_count + 1, 0, -1
            )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per block
            for seq in itertools.combinations_with_replacement(
                range(1, blob_count + 2), i
            )  # We iterate through all possible combinations
            if sum(seq) == blob_count  # And we only keep the ones that match the
            # expected invalid blob count
        ]

        # We also add the reversed version of each combination, only if it's not
        # already in the list. E.g. (4, 1) is added from (1, 4) but not
        # (1, 1, 1, 1, 1) because its reversed version is identical.
        combinations += [
            tuple(reversed(x)) for x in combinations if tuple(reversed(x)) not in combinations
        ]
        return combinations

    @classmethod
    def all_valid_blob_combinations(cls, fork: Fork) -> List[Tuple[int, ...]]:
        """
        Return all valid blob tx combinations for a given block,
        assuming the given MAX_BLOBS_PER_BLOCK.
        """
        max_blobs_per_block = fork.max_blobs_per_block()
        combinations: List[Tuple[int, ...]] = []
        for i in range(1, max_blobs_per_block + 1):
            combinations += cls.get_blob_combinations(i)
        return combinations

    @classmethod
    def invalid_blob_combinations(cls, fork: Fork) -> List[Tuple[int, ...]]:
        """
        Return invalid blob tx combinations for a given block that use up to
        MAX_BLOBS_PER_BLOCK+1 blobs.
        """
        max_blobs_per_block = fork.max_blobs_per_block()
        return cls.get_blob_combinations(max_blobs_per_block + 1)
