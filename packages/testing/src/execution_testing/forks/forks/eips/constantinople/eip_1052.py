"""
EIP-1052: EXTCODEHASH opcode.

Provide a new opcode that returns the keccak256 hash of a contract's
code.

https://eips.ethereum.org/EIPS/eip-1052
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP1052(BaseFork):
    """EIP-1052 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add EXTCODEHASH opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP1052, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.EXTCODEHASH: cls._with_account_access(0, gas_costs),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add EXTCODEHASH to valid opcodes."""
        return [
            Opcodes.EXTCODEHASH,
        ] + super(EIP1052, cls).valid_opcodes()
