"""
EIP-152: Add BLAKE2 compression function F precompile.

https://eips.ethereum.org/EIPS/eip-152
"""

from dataclasses import replace
from typing import List

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP152(BaseFork):
    """EIP-152 class."""

    @classmethod
    def precompiles(cls) -> List[Address]:
        """Add BLAKE2 compression function precompile."""
        return [
            Address(9, label="BLAKE2F"),
        ] + super(EIP152, cls).precompiles()

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Set BLAKE2F per-round gas cost."""
        return replace(
            super(EIP152, cls).gas_costs(),
            GAS_PRECOMPILE_BLAKE2F_PER_ROUND=1,
        )
