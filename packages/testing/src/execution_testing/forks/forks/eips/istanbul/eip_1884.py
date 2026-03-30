"""
EIP-1884: Repricing for trie-size-dependent opcodes.

Introduces SELFBALANCE opcode.

https://eips.ethereum.org/EIPS/eip-1884
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP1884(BaseFork):
    """EIP-1884 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add SELFBALANCE opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP1884, cls).opcode_gas_map()
        return {**base_map, Opcodes.SELFBALANCE: gas_costs.GAS_LOW}

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SELFBALANCE to valid opcodes."""
        return [
            Opcodes.SELFBALANCE,
        ] + super(EIP1884, cls).valid_opcodes()
