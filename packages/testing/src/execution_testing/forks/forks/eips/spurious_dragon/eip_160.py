"""
EIP-160: EXP cost increase.

Raise the per-byte charge for EXP's exponent operand from 10 to 50.

https://eips.ethereum.org/EIPS/eip-160
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP160(BaseFork):
    """EIP-160 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Raise the EXP per-exponent-byte gas cost to 50."""
        return replace(
            super(EIP160, cls).gas_costs(),
            OPCODE_EXP_PER_BYTE=50,
        )
