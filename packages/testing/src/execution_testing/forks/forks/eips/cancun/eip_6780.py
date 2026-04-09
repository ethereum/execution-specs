"""
EIP-6780: SELFDESTRUCT only in same transaction.

SELFDESTRUCT will recover all funds to the target but not delete the account,
except when called in the same transaction as creation.

https://eips.ethereum.org/EIPS/eip-6780
"""

from ....base_fork import BaseFork


class EIP6780(BaseFork):
    """EIP-6780 class."""

    pass
