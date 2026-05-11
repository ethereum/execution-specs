"""
EIP-1344: ChainID opcode.

Add a new opcode that returns the current chain's EIP-155 unique
identifier.

https://eips.ethereum.org/EIPS/eip-1344
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP1344(BaseFork):
    """EIP-1344 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add CHAINID opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP1344, cls).opcode_gas_map()
        return {**base_map, Opcodes.CHAINID: gas_costs.BASE}

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add CHAINID to valid opcodes."""
        return [Opcodes.CHAINID] + super(EIP1344, cls).valid_opcodes()
