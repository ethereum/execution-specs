"""Defines EIP-7918 specification constants and functions."""

from dataclasses import dataclass

# Base the spec on EIP-4844 which EIP-7918 extends
from ...cancun.eip4844_blobs.spec import Spec as EIP4844Spec


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7918 = ReferenceSpec("EIPS/eip-7918.md", "be1dbefafcb40879e3f6d231fad206c62f5b371b")


@dataclass(frozen=True)
class Spec(EIP4844Spec):
    """
    Parameters from the EIP-7918 specifications.
    Extends EIP-4844 spec with the new reserve price constant and functionality.
    """

    BLOB_BASE_COST = 2**14

    @classmethod
    def get_reserve_price(
        cls,
        base_fee_per_gas: int,
    ) -> int:
        """Calculate the reserve price for blob gas given the blob base fee."""
        return (cls.BLOB_BASE_COST * base_fee_per_gas) // cls.GAS_PER_BLOB

    @classmethod
    def is_reserve_price_active(
        cls,
        base_fee_per_gas: int,
        blob_base_fee: int,
    ) -> bool:
        """Check if the reserve price mechanism should be active."""
        reserve_price = cls.get_reserve_price(base_fee_per_gas)
        return reserve_price > blob_base_fee

    @classmethod
    def calc_effective_blob_base_fee(
        cls,
        base_fee_per_gas: int,
        blob_base_fee: int,
    ) -> int:
        """Calculate the effective blob base fee considering the reserve price."""
        reserve_price = cls.get_reserve_price(base_fee_per_gas)
        return max(reserve_price, blob_base_fee)
