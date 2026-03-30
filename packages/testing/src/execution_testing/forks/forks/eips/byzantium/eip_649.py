"""
EIP-649: Metropolis difficulty bomb delay and block reward reduction.

Delay the difficulty bomb and reduce the block reward to 3 ETH.

https://eips.ethereum.org/EIPS/eip-649
"""

from ....base_fork import BaseFork


class EIP649(BaseFork):
    """EIP-649 class."""

    @classmethod
    def get_reward(cls) -> int:
        """Block reward is reduced to 3 ETH."""
        return 3_000_000_000_000_000_000
