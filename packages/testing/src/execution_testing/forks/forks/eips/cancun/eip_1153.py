"""
EIP-1153: Transient storage opcodes.

Add opcodes for manipulating state that behaves identically to storage
but is discarded after every transaction.

https://eips.ethereum.org/EIPS/eip-1153
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP1153(BaseFork):
    """EIP-1153 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add TLOAD and TSTORE opcode gas costs."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP1153, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.TLOAD: gas_costs.GAS_WARM_SLOAD,
            Opcodes.TSTORE: gas_costs.GAS_WARM_SLOAD,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add TLOAD and TSTORE to valid opcodes."""
        return [
            Opcodes.TLOAD,
            Opcodes.TSTORE,
        ] + super(EIP1153, cls).valid_opcodes()
