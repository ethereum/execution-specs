"""
EIP-1234: Constantinople difficulty bomb delay and block reward adjustment.

Delay the difficulty bomb and reduce the block reward to 2 ETH.

https://eips.ethereum.org/EIPS/eip-1234
"""

from ....base_fork import BaseFork


class EIP1234(BaseFork):
    """EIP-1234 class."""

    @classmethod
    def get_reward(cls) -> int:
        """Block reward is reduced to 2 ETH."""
        return 2_000_000_000_000_000_000
