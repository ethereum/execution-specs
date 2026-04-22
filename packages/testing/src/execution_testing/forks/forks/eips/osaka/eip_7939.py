"""
EIP-7939: CLZ (Count Leading Zeros) EVM opcode.

Opcode to count the number of leading zero bits in a 256-bit word.

https://eips.ethereum.org/EIPS/eip-7939
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP7939(BaseFork):
    """EIP-7939 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add CLZ opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP7939, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.CLZ: gas_costs.GAS_LOW,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add CLZ to valid opcodes."""
        return [
            Opcodes.CLZ,
        ] + super(EIP7939, cls).valid_opcodes()
