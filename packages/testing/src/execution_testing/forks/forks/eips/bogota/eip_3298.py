"""
EIP-3298: Remove storage-clear refund and refund cap.

Drop the storage-clearing refund and the transaction refund cap,
leaving only the net-metered storage write reversal.

https://eips.ethereum.org/EIPS/eip-3298
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP3298(BaseFork):
    """EIP-3298 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Remove the storage clearing refund."""
        return replace(
            super(EIP3298, cls).gas_costs(),
            REFUND_STORAGE_CLEAR=0,
        )

    @classmethod
    def max_refund_quotient(cls) -> int:
        """
        Refunds are no longer capped. A quotient of one caps the refund
        at the whole gas used, which the remaining refund rule can never
        exceed, so every call site keeps its `min` and stays correct.
        """
        return 1
