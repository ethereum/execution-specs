"""
EIP-196: Precompiled contracts for addition and scalar multiplication on
the elliptic curve alt_bn128.

https://eips.ethereum.org/EIPS/eip-196
"""

from dataclasses import replace
from typing import List

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP196(BaseFork):
    """EIP-196 class."""

    @classmethod
    def precompiles(cls) -> List[Address]:
        """Add BN254 addition and scalar multiplication precompiles."""
        return [
            Address(6, label="BN254_ADD"),
            Address(7, label="BN254_MUL"),
        ] + super(EIP196, cls).precompiles()

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Set gas costs for BN254 addition and multiplication."""
        return replace(
            super(EIP196, cls).gas_costs(),
            GAS_PRECOMPILE_ECADD=500,
            GAS_PRECOMPILE_ECMUL=40_000,
        )
