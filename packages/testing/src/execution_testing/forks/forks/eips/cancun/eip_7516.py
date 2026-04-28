"""
EIP-7516: BLOBBASEFEE instruction.

Instruction that returns the current data-blob base-fee.

https://eips.ethereum.org/EIPS/eip-7516
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP7516(BaseFork):
    """EIP-7516 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add BLOBBASEFEE opcode gas cost."""
        gas_costs = cls.gas_costs()

        # Get parent fork's opcode gas map
        base_map = super(EIP7516, cls).opcode_gas_map()

        # Add Cancun-specific opcodes
        return {
            **base_map,
            Opcodes.BLOBBASEFEE: gas_costs.BASE,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add BLOBBASEFEE to valid opcodes."""
        return [
            Opcodes.BLOBBASEFEE,
        ] + super(EIP7516, cls).valid_opcodes()
