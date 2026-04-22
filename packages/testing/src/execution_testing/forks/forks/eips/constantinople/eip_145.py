"""
EIP-145: Bitwise shifting instructions in EVM.

Add SHL, SHR, and SAR instructions to the EVM.

https://eips.ethereum.org/EIPS/eip-145
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP145(BaseFork):
    """EIP-145 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add SHL, SHR, and SAR opcode gas costs."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP145, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.SHL: gas_costs.GAS_VERY_LOW,
            Opcodes.SHR: gas_costs.GAS_VERY_LOW,
            Opcodes.SAR: gas_costs.GAS_VERY_LOW,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SHL, SHR, and SAR to valid opcodes."""
        return [
            Opcodes.SHL,
            Opcodes.SHR,
            Opcodes.SAR,
        ] + super(EIP145, cls).valid_opcodes()
