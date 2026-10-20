"""
EIP-8198: Quick Slots.

Reduce the consensus-layer slot duration. The execution layer scales the
maximum per-block base fee change with the slot duration, read from the
spacing of a block and its parent, so that fee dynamics per unit of wall-clock
time stay close to their previous values.

https://eips.ethereum.org/EIPS/eip-8198
"""

from ....base_fork import (
    DEFAULT_SECONDS_ELAPSED,
    DEFAULT_SLOTS_ELAPSED,
    BaseFork,
)

BASE_FEE_REFERENCE_SLOT_SECONDS = 12
"""
Slot duration at which the maximum base fee change per block is the parent
fork's.
"""


class EIP8198(BaseFork):
    """EIP-8198 class."""

    @classmethod
    def base_fee_follows_slot_spacing(cls) -> bool:
        """
        The maximum base fee change follows the slot duration read from the
        block spacing.
        """
        return True

    @classmethod
    def base_fee_max_change_numerator(
        cls,
        *,
        seconds_elapsed: int = DEFAULT_SECONDS_ELAPSED,
        slots_elapsed: int = DEFAULT_SLOTS_ELAPSED,
    ) -> int:
        """
        The maximum base fee change per block scales with the slot duration,
        `seconds_elapsed / slots_elapsed`, read from the block spacing, and
        never exceeds the parent fork's maximum change.
        """
        return min(
            seconds_elapsed, BASE_FEE_REFERENCE_SLOT_SECONDS * slots_elapsed
        )

    @classmethod
    def base_fee_max_change_denominator(
        cls,
        *,
        seconds_elapsed: int = DEFAULT_SECONDS_ELAPSED,
        slots_elapsed: int = DEFAULT_SLOTS_ELAPSED,
    ) -> int:
        """
        The maximum base fee change per block is the parent fork's at
        twelve-second slots.
        """
        del seconds_elapsed
        parent_denominator = super(
            EIP8198, cls
        ).base_fee_max_change_denominator()
        return (
            parent_denominator
            * BASE_FEE_REFERENCE_SLOT_SECONDS
            * slots_elapsed
        )
