"""
EIP-8141: Frame Transaction.

Add a new transaction type constructed from a series of frames,
abstractly defining validity conditions and gas payment.

https://eips.ethereum.org/EIPS/eip-8141
"""

from typing import List

from ....base_fork import BaseFork


class EIP8141(BaseFork):
    """EIP-8141 class."""

    @classmethod
    def tx_types(cls) -> List[int]:
        """Frame transactions (type 6) are introduced."""
        return super(EIP8141, cls).tx_types() + [6]
