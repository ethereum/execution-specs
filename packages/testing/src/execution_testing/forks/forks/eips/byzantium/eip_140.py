"""
EIP-140: REVERT instruction.

Provide a way to stop execution and revert state changes without consuming
all provided gas.

https://eips.ethereum.org/EIPS/eip-140
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP140(BaseFork):
    """EIP-140 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add REVERT opcode gas cost."""
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP140, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.REVERT: cls._with_memory_expansion(
                0, memory_expansion_calculator
            ),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add REVERT to valid opcodes."""
        return [Opcodes.REVERT] + super(EIP140, cls).valid_opcodes()
