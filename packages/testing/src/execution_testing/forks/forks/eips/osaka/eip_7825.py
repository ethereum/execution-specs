"""
EIP-7825: Transaction gas limit cap.

Introduce a protocol-level cap on the maximum gas used by a transaction to
16,777,216 (2^24).

https://eips.ethereum.org/EIPS/eip-7825
"""

from ....base_fork import BaseFork


class EIP7825(BaseFork):
    """EIP-7825 class."""

    @classmethod
    def transaction_gas_limit_cap(cls) -> int | None:
        """Transaction gas limit is capped at 16 million (2**24)."""
        return 16_777_216
