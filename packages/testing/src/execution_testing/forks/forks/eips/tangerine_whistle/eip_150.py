"""
EIP-150: Gas cost changes for IO-heavy operations.

Reprice the flat account and storage access costs. Only the costs
consumed by the opcode gas model are modeled here.

https://eips.ethereum.org/EIPS/eip-150
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP150(BaseFork):
    """EIP-150 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Reprice the IO-heavy opcodes."""
        return replace(
            super(EIP150, cls).gas_costs(),
            OPCODE_BALANCE=400,
            OPCODE_EXTERNAL_BASE=700,
            OPCODE_CALL_BASE=700,
            OPCODE_SLOAD=200,
            OPCODE_SELFDESTRUCT_BASE=5_000,
        )
