"""
EIP-3298: Remove storage-clear refund and refund cap.

Drop the storage-clearing refund and the transaction refund cap,
leaving only the net-metered storage write reversal.

https://eips.ethereum.org/EIPS/eip-3298
"""

from dataclasses import replace
from typing import List

from ....base_fork import BaseFork, RefundTypes
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

    @classmethod
    def refund_types(cls) -> List[RefundTypes]:
        """
        Clearing a slot no longer refunds; restoring one to its original
        value still does.
        """
        refunds: List[RefundTypes] = [
            refund_type
            for refund_type in super(EIP3298, cls).refund_types()
            if refund_type != RefundTypes.STORAGE_CLEAR
        ]
        refunds.append(RefundTypes.STORAGE_RESTORE)
        return refunds
