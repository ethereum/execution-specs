"""
EIP-8198: Quick Slots.

Reduce the consensus-layer slot duration. The execution layer lowers the
maximum per-block base fee change and updates the blob schedule so that fee
dynamics and blob throughput per unit of wall-clock time stay close to their
previous values.

https://eips.ethereum.org/EIPS/eip-8198
"""

from ....base_fork import BaseFork


class EIP8198(
    BaseFork,
    # Provisional values, pending a joint decision with the consensus layer.
    update_blob_constants={
        "TARGET_BLOBS_PER_BLOCK": 12,
        "MAX_BLOBS_PER_BLOCK": 18,
        "BLOB_BASE_FEE_UPDATE_FRACTION": 12018519,
    },
):
    """EIP-8198 class."""

    @classmethod
    def base_fee_max_change_numerator(cls) -> int:
        """The maximum base fee change per block is lowered to 5/48."""
        return 5

    @classmethod
    def base_fee_max_change_denominator(cls) -> int:
        """The maximum base fee change per block is lowered to 5/48."""
        return 48
