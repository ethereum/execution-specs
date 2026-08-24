"""
EIP-8368: CPSB Recalibration for New Gas Limit.

https://eips.ethereum.org/EIPS/eip-8368
"""

from ....base_fork import BaseFork


class EIP8368(BaseFork):
    """EIP-8368 class."""

    @classmethod
    def cost_per_state_byte(cls) -> int:
        """
        Return the recalibrated cost per state byte.

        Provisional value from the EIP-8037 derivation at a 300M
        reference block gas limit. The EIP leaves the reference limit
        and the value TBD.
        """
        return 3060
