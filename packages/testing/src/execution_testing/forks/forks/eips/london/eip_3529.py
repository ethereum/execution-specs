"""
EIP-3529: Reduction in refunds.

Remove gas refunds for SELFDESTRUCT and reduce refunds for SSTORE.

https://eips.ethereum.org/EIPS/eip-3529
"""

from ....base_fork import BaseFork


class EIP3529(BaseFork):
    """EIP-3529 class."""

    @classmethod
    def max_refund_quotient(cls) -> int:
        """Max refund quotient is increased to 5 (reducing refunds)."""
        return 5
