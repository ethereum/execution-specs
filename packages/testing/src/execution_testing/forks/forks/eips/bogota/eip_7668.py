"""
EIP-7668: Remove bloom filters.

The logs bloom of a block header and of a transaction receipt is empty.

https://eips.ethereum.org/EIPS/eip-7668
"""

from execution_testing.base_types import Bloom

from ....base_fork import BaseFork


class EIP7668(BaseFork):
    """EIP-7668 class."""

    @classmethod
    def empty_logs_bloom(cls) -> Bloom:
        """The logs bloom is empty regardless of the logs emitted."""
        return Bloom(b"")
