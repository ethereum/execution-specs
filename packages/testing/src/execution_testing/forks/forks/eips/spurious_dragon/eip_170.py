"""
EIP-170: Contract code size limit.

https://eips.ethereum.org/EIPS/eip-170
"""

from ....base_fork import BaseFork


class EIP170(BaseFork):
    """EIP-170 class."""

    @classmethod
    def max_code_size(cls) -> int:
        """Upper bound is introduced for max contract code size."""
        return 0x6000
