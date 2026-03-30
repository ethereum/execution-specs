"""
EIP-211: New opcodes: RETURNDATASIZE and RETURNDATACOPY.

https://eips.ethereum.org/EIPS/eip-211
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP211(BaseFork):
    """EIP-211 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add RETURNDATASIZE and RETURNDATACOPY opcode gas costs."""
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP211, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.RETURNDATASIZE: gas_costs.GAS_BASE,
            Opcodes.RETURNDATACOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.GAS_VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add RETURNDATASIZE and RETURNDATACOPY to valid opcodes."""
        return [
            Opcodes.RETURNDATASIZE,
            Opcodes.RETURNDATACOPY,
        ] + super(EIP211, cls).valid_opcodes()
