"""
EIP-8024: Backward compatible SWAPN, DUPN, EXCHANGE.

Introduce additional instructions for manipulating the stack which allow
accessing the stack at higher depths.

https://eips.ethereum.org/EIPS/eip-8024
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP8024(BaseFork):
    """EIP-8024 class."""

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SWAPN, DUPN, EXCHANGE."""
        return [
            Opcodes.SWAPN,
            Opcodes.DUPN,
            Opcodes.EXCHANGE,
        ] + super(EIP8024, cls).valid_opcodes()

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add gas costs for SWAPN, DUPN, EXCHANGE."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP8024, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.SWAPN: gas_costs.GAS_VERY_LOW,
            Opcodes.DUPN: gas_costs.GAS_VERY_LOW,
            Opcodes.EXCHANGE: gas_costs.GAS_VERY_LOW,
        }
