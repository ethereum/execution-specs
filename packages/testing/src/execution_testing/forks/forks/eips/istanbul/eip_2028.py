"""
EIP-2028: Transaction data gas cost reduction.

Reduce the gas cost of non-zero transaction data bytes to 16.

https://eips.ethereum.org/EIPS/eip-2028
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP2028(BaseFork):
    """EIP-2028 class."""

    @classmethod
    def gas_costs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> GasCosts:
        """Reduce non-zero calldata byte gas cost to 16."""
        del block_number, timestamp
        return replace(
            super(EIP2028, cls).gas_costs(),
            TX_DATA_PER_NON_ZERO=16,
        )
