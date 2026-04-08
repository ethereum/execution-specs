"""
EIP-2537: Precompile for BLS12-381 curve operations.

Adds operations on BLS12-381 curve as precompiles in a set necessary to
efficiently perform operations such as BLS signature verification.

https://eips.ethereum.org/EIPS/eip-2537
"""

from dataclasses import replace
from typing import List

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP2537(BaseFork):
    """EIP-2537 class."""

    @classmethod
    def precompiles(cls) -> List[Address]:
        """
        Add precompiles for BLS12-381 curve operations.

        BLS12_G1ADD = 0x0B
        BLS12_G1MSM = 0x0C
        BLS12_G2ADD = 0x0D
        BLS12_G2MSM = 0x0E
        BLS12_PAIRING_CHECK = 0x0F
        BLS12_MAP_FP_TO_G1 = 0x10
        BLS12_MAP_FP2_TO_G2 = 0x11
        """
        return [
            Address(11, label="BLS12_G1ADD"),
            Address(12, label="BLS12_G1MSM"),
            Address(13, label="BLS12_G2ADD"),
            Address(14, label="BLS12_G2MSM"),
            Address(15, label="BLS12_PAIRING_CHECK"),
            Address(16, label="BLS12_MAP_FP_TO_G1"),
            Address(17, label="BLS12_MAP_FP2_TO_G2"),
        ] + super(EIP2537, cls).precompiles()

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add gas costs for BLS12-381 precompiles."""
        return replace(
            super(EIP2537, cls).gas_costs(),
            PRECOMPILE_BLS_G1ADD=375,
            PRECOMPILE_BLS_G1MUL=12_000,
            PRECOMPILE_BLS_G1MAP=5_500,
            PRECOMPILE_BLS_G2ADD=600,
            PRECOMPILE_BLS_G2MUL=22_500,
            PRECOMPILE_BLS_G2MAP=23_800,
            PRECOMPILE_BLS_PAIRING_BASE=37_700,
            PRECOMPILE_BLS_PAIRING_PER_PAIR=32_600,
        )
