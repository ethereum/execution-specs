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
        is capped at the whole base fee.
        """
        return min(seconds_elapsed, 8 * 12 * slots_elapsed)

    @classmethod
    def base_fee_max_change_denominator(
        cls,
        *,
        seconds_elapsed: int = DEFAULT_SECONDS_ELAPSED,
        slots_elapsed: int = DEFAULT_SLOTS_ELAPSED,
    ) -> int:
        """
        The maximum base fee change per block is `1/8` at twelve-second
        slots: `seconds_elapsed / (8 * 12 * slots_elapsed)`.
        """
        del seconds_elapsed
        return 8 * 12 * slots_elapsed
