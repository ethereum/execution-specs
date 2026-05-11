"""
EIP-3855: PUSH0 instruction.

Introduce a new instruction which pushes the constant value 0 onto the
stack.

https://eips.ethereum.org/EIPS/eip-3855
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP3855(BaseFork):
    """EIP-3855 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add PUSH0 opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP3855, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.PUSH0: gas_costs.BASE,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add PUSH0 to valid opcodes."""
        return [Opcodes.PUSH0] + super(EIP3855, cls).valid_opcodes()
