"""
EIP-5656: MCOPY - Memory copying instruction.

An efficient EVM instruction for copying memory areas.

https://eips.ethereum.org/EIPS/eip-5656
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP5656(BaseFork):
    """EIP-5656 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add MCOPY opcode gas cost."""
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP5656, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.MCOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add MCOPY to valid opcodes."""
        return [
            Opcodes.MCOPY,
        ] + super(EIP5656, cls).valid_opcodes()
