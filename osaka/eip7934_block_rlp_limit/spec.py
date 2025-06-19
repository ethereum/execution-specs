"""Defines EIP-7934 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7934 = ReferenceSpec("EIPS/eip-7934.md", "028e8657abdf9fa3f2159e639bccd2f66f88be1c")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7934 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7934#specification.
    """

    MAX_BLOCK_SIZE = 10_485_760  # 10 MiB
    SAFETY_MARGIN = 2_097_152  # 2 MiB
    MAX_RLP_BLOCK_SIZE = MAX_BLOCK_SIZE - SAFETY_MARGIN  # 8_388_608 bytes

    @staticmethod
    def exceed_max_rlp_block_size(rlp_encoded_block: bytes) -> bool:
        """Check if an RLP encoded block exceeds the maximum allowed size."""
        return len(rlp_encoded_block) > Spec.MAX_RLP_BLOCK_SIZE
