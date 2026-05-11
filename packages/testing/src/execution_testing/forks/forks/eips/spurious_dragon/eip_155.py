"""
EIP-155: Simple replay attack protection.

https://eips.ethereum.org/EIPS/eip-155
"""

from ....base_fork import BaseFork


class EIP155(BaseFork):
    """EIP-155 class."""

    @classmethod
    def supports_protected_txs(cls) -> bool:
        """
        Enables support for protected transactions.
        """
        return True
