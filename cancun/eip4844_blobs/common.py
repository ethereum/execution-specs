"""Common constants, classes & functions local to EIP-4844 tests."""

from dataclasses import dataclass
from typing import List, Literal, Tuple

from .spec import Spec

INF_POINT = (0xC0 << 376).to_bytes(48, byteorder="big")
Z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
Z_Y_INVALID_ENDIANNESS: Literal["little", "big"] = "little"
Z_Y_VALID_ENDIANNESS: Literal["little", "big"] = "big"


@dataclass(kw_only=True)
class Blob:
    """Class representing a full blob."""

    blob: bytes
    kzg_commitment: bytes
    kzg_proof: bytes

    def versioned_hash(self) -> bytes:
        """Calculate versioned hash for a given blob."""
        return Spec.kzg_to_versioned_hash(self.kzg_commitment)

    @staticmethod
    def blobs_to_transaction_input(
        input_blobs: List["Blob"],
    ) -> Tuple[List[bytes], List[bytes], List[bytes]]:
        """
        Return tuple of lists of blobs, kzg commitments formatted to be added to a network blob
        type transaction.
        """
        blobs: List[bytes] = []
        kzg_commitments: List[bytes] = []
        kzg_proofs: List[bytes] = []

        for blob in input_blobs:
            blobs.append(blob.blob)
            kzg_commitments.append(blob.kzg_commitment)
            kzg_proofs.append(blob.kzg_proof)
        return (blobs, kzg_commitments, kzg_proofs)
