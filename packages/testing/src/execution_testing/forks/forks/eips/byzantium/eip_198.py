"""
EIP-198: Big integer modular exponentiation.

Precompile for modular exponentiation.

https://eips.ethereum.org/EIPS/eip-198
"""

from typing import List

from execution_testing.base_types import Address

from ....base_fork import BaseFork


class EIP198(BaseFork):
    """EIP-198 class."""

    @classmethod
    def precompiles(cls) -> List[Address]:
        """Add modular exponentiation precompile."""
        return [
            Address(5, label="MODEXP"),
        ] + super(EIP198, cls).precompiles()
