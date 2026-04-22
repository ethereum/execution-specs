"""
EIP-3198: BASEFEE opcode.

Add an opcode that returns the value of the base fee of the current
block.

https://eips.ethereum.org/EIPS/eip-3198
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP3198(BaseFork):
    """EIP-3198 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add BASEFEE opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP3198, cls).opcode_gas_map()
        return {**base_map, Opcodes.BASEFEE: gas_costs.GAS_BASE}

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add BASEFEE to valid opcodes."""
        return [Opcodes.BASEFEE] + super(EIP3198, cls).valid_opcodes()
