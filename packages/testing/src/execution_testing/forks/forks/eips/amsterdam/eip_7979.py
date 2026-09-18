"""
EIP-7979: Call and Return Opcodes for the EVM.

Three instructions and a return stack: CALLSUB, CALLDEST and RETURNSUB.

https://eips.ethereum.org/EIPS/eip-7979
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP7979(BaseFork):
    """EIP-7979 class."""

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add CALLSUB, CALLDEST and RETURNSUB to valid opcodes."""
        return [
            Opcodes.CALLSUB,
            Opcodes.CALLDEST,
            Opcodes.RETURNSUB,
        ] + super(EIP7979, cls).valid_opcodes()

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add the gas costs of CALLSUB, CALLDEST and RETURNSUB."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP7979, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.CALLSUB: gas_costs.MID,
            Opcodes.CALLDEST: gas_costs.OPCODE_JUMPDEST,
            Opcodes.RETURNSUB: gas_costs.LOW,
        }
