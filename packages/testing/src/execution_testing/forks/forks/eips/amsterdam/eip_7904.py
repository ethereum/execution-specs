"""
EIP-7904: Gas Repricing.

Reprice arithmetic opcodes and a number of precompiles based on benchmark
results.

https://eips.ethereum.org/EIPS/eip-7904
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP7904(BaseFork):
    """EIP-7904 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Apply EIP-7904 gas repricing."""
        return replace(
            super(EIP7904, cls).gas_costs(),
            # Opcodes
            OPCODE_SDIV=6,
            OPCODE_MOD=6,
            OPCODE_SMOD=6,
            OPCODE_MULMOD=12,
            # Precompiles
            PRECOMPILE_BLAKE2F_BASE=48,
            PRECOMPILE_ECADD=382,
            PRECOMPILE_P256VERIFY=15_958,
            PRECOMPILE_POINT_EVALUATION=84_081,
        )
