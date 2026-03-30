"""
EIP-197: Precompiled contracts for optimal ate pairing check on the
elliptic curve alt_bn128.

https://eips.ethereum.org/EIPS/eip-197
"""

from dataclasses import replace
from typing import List

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP197(BaseFork):
    """EIP-197 class."""

    @classmethod
    def precompiles(cls) -> List[Address]:
        """Add BN254 pairing check precompile."""
        return [
            Address(8, label="BN254_PAIRING"),
        ] + super(EIP197, cls).precompiles()

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Set gas costs for BN254 pairing check."""
        return replace(
            super(EIP197, cls).gas_costs(),
            GAS_PRECOMPILE_ECPAIRING_BASE=100_000,
            GAS_PRECOMPILE_ECPAIRING_PER_POINT=80_000,
        )
