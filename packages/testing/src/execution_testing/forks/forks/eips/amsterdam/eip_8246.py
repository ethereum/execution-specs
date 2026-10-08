"""
EIP-8246: Remove SELFDESTRUCT balance burn.

https://eips.ethereum.org/EIPS/eip-8246
"""

from ....base_fork import BaseFork


class EIP8246(BaseFork):
    """EIP-8246 class."""

    @classmethod
    def selfdestruct_burns_balance(cls) -> bool:
        """SELFDESTRUCT no longer burns ether."""
        return False
