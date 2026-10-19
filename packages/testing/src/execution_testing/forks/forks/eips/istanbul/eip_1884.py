"""
EIP-1884: Repricing for trie-size-dependent opcodes.

Introduces SELFBALANCE opcode.

https://eips.ethereum.org/EIPS/eip-1884
"""

from dataclasses import replace
from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP1884(BaseFork):
    """EIP-1884 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Reprice the trie-size-dependent opcodes."""
        return replace(
            super(EIP1884, cls).gas_costs(),
            OPCODE_BALANCE=700,
            OPCODE_SLOAD=800,
            OPCODE_EXTCODEHASH=700,
        )

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add SELFBALANCE opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP1884, cls).opcode_gas_map()
        return {**base_map, Opcodes.SELFBALANCE: gas_costs.LOW}

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SELFBALANCE to valid opcodes."""
        return [
            Opcodes.SELFBALANCE,
        ] + super(EIP1884, cls).valid_opcodes()
