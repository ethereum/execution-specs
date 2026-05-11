"""
EIP-1108: Reduce alt_bn128 precompile gas costs.

https://eips.ethereum.org/EIPS/eip-1108
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP1108(BaseFork):
    """EIP-1108 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Reduce BN254 precompile gas costs."""
        return replace(
            super(EIP1108, cls).gas_costs(),
            PRECOMPILE_ECADD=150,
            PRECOMPILE_ECMUL=6000,
            PRECOMPILE_ECPAIRING_BASE=45_000,
            PRECOMPILE_ECPAIRING_PER_POINT=34_000,
        )
