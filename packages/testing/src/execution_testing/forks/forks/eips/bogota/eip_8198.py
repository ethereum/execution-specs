"""
EIP-8198: Quick Slots.

Reduce the consensus-layer slot duration. The execution layer lowers the
maximum per-block base fee change so that fee dynamics per unit of wall-clock
time stay close to their previous values.

https://eips.ethereum.org/EIPS/eip-8198
"""

from ....base_fork import BaseFork


class EIP8198(BaseFork):
    """EIP-8198 class."""

    @classmethod
    def base_fee_max_change_numerator(cls) -> int:
        """The maximum base fee change per block is lowered to 5/48."""
        return 5

    @classmethod
    def base_fee_max_change_denominator(cls) -> int:
        """The maximum base fee change per block is lowered to 5/48."""
        return 48
