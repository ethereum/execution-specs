"""
EIP-7918: Blob base fee bounded by execution cost.

Imposes that the price of GAS_PER_BLOB blob gas is greater than the price
of BLOB_BASE_COST execution gas.

https://eips.ethereum.org/EIPS/eip-7918
"""

from ....base_fork import BaseFork, ExcessBlobGasCalculator


class EIP7918(
    BaseFork,
    update_blob_constants={
        "BLOB_BASE_COST": 2**13,
    },
):
    """EIP-7918 class."""

    @classmethod
    def excess_blob_gas_calculator(cls) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block.
        """
        target_blobs_per_block = cls.target_blobs_per_block()
        blob_gas_per_blob = cls.blob_gas_per_blob()
        blob_target_gas_per_block = target_blobs_per_block * blob_gas_per_blob
        max_blobs_per_block = cls.max_blobs_per_block()
        blob_base_cost = cls.blob_base_cost()

        def fn(
            *,
            parent_excess_blob_gas: int | None = None,
            parent_excess_blobs: int | None = None,
            parent_blob_gas_used: int | None = None,
            parent_blob_count: int | None = None,
            parent_base_fee_per_gas: int,
        ) -> int:
            if parent_excess_blob_gas is None:
                assert parent_excess_blobs is not None, (
                    "Parent excess blobs are required"
                )
                parent_excess_blob_gas = (
                    parent_excess_blobs * blob_gas_per_blob
                )
            if parent_blob_gas_used is None:
                assert parent_blob_count is not None, (
                    "Parent blob count is required"
                )
                parent_blob_gas_used = parent_blob_count * blob_gas_per_blob
            if (
                parent_excess_blob_gas + parent_blob_gas_used
                < blob_target_gas_per_block
            ):
                return 0

            # EIP-7918: Apply reserve price when execution costs dominate
            # blob costs
            current_blob_base_fee = cls.blob_gas_price_calculator()(
                excess_blob_gas=parent_excess_blob_gas
            )
            reserve_price_active = (
                blob_base_cost * parent_base_fee_per_gas
                > blob_gas_per_blob * current_blob_base_fee
            )
            if reserve_price_active:
                blob_excess_adjustment = (
                    parent_blob_gas_used
                    * (max_blobs_per_block - target_blobs_per_block)
                    // max_blobs_per_block
                )
                return parent_excess_blob_gas + blob_excess_adjustment

            # Original EIP-4844 calculation
            return (
                parent_excess_blob_gas
                + parent_blob_gas_used
                - blob_target_gas_per_block
            )

        return fn

    @classmethod
    def blob_reserve_price_active(cls) -> bool:
        """Blob reserve price is supported."""
        return True
