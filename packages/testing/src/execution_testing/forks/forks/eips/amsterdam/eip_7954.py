"""
EIP-7954: Increase Maximum Contract Size.

Raise the maximum contract code size from 24KiB to 32KiB and initcode size from
48KiB to 64KiB.

https://eips.ethereum.org/EIPS/eip-7954
"""

from ....base_fork import BaseFork


class EIP7954(BaseFork):
    """EIP-7954 class."""

    @classmethod
    def max_code_size(cls) -> int:
        """Max contract code size is 32 KiB."""
        return 32 * 1024

    @classmethod
    def max_initcode_size(cls) -> int:
        """Max initcode size is 64 KiB."""
        return 64 * 1024
