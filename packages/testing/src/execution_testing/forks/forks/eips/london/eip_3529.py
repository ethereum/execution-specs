"""
EIP-3529: Reduction in refunds.

Remove gas refunds for SELFDESTRUCT and reduce refunds for SSTORE.

https://eips.ethereum.org/EIPS/eip-3529
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP3529(BaseFork):
    """EIP-3529 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Storage clearing refund is reduced from 15000 to 4800."""
        return replace(
            super(EIP3529, cls).gas_costs(),
            REFUND_STORAGE_CLEAR=4_800,
        )

    @classmethod
    def max_refund_quotient(cls) -> int:
        """Max refund quotient is increased to 5 (reducing refunds)."""
        return 5
