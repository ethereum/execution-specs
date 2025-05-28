"""Blob-related types for Ethereum tests."""

from hashlib import sha256
from typing import List

from ethereum_test_base_types import Bytes, CamelModel, Hash


class Blob(CamelModel):
    """Class representing a full blob."""

    data: Bytes
    kzg_commitment: Bytes
    kzg_proof: Bytes | None = None
    kzg_cell_proofs: List[Bytes] | None = None

    def versioned_hash(self, version: int = 1) -> Hash:
        """Calculate versioned hash for a given blob."""
        return Hash(bytes([version]) + sha256(self.kzg_commitment).digest()[1:])
