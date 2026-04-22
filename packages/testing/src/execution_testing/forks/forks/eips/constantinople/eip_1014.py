"""
EIP-1014: Skinny CREATE2.

Add a new CREATE2 opcode that uses keccak256 for address derivation.

https://eips.ethereum.org/EIPS/eip-1014
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP1014(BaseFork):
    """EIP-1014 class."""

    @classmethod
    def _calculate_create2_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate CREATE2 gas cost based on metadata."""
        metadata = opcode.metadata

        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        hash_gas = gas_costs.GAS_KECCAK256_PER_WORD * init_code_words

        return gas_costs.GAS_CREATE + hash_gas

    @classmethod
    def create_opcodes(cls) -> List[Opcodes]:
        """Add CREATE2 opcode."""
        return [
            Opcodes.CREATE2,
        ] + super(EIP1014, cls).create_opcodes()

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add CREATE2 opcode gas cost."""
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP1014, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.CREATE2: cls._with_memory_expansion(
                lambda op: cls._calculate_create2_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add CREATE2 to valid opcodes."""
        return [
            Opcodes.CREATE2,
        ] + super(EIP1014, cls).valid_opcodes()
