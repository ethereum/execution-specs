"""
EIP-8298: SETCODEFROM Code Reuse Instruction.

Adds an instruction that sets an account's code hash from an existing
deployed contract.

https://eips.ethereum.org/EIPS/eip-8298
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP8298(BaseFork):
    """EIP-8298 class."""

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SETCODEFROM."""
        return [Opcodes.SETCODEFROM] + super(EIP8298, cls).valid_opcodes()

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add the SETCODEFROM gas cost."""
        gas_costs = cls.gas_costs()
        return {
            **super(EIP8298, cls).opcode_gas_map(),
            Opcodes.SETCODEFROM: lambda op: cls._calculate_setcodefrom_gas(
                op, gas_costs
            ),
        }

    @classmethod
    def _calculate_setcodefrom_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Charge the source lookup, then the current-account access for a
        valid source, then the write for a changed code hash.
        """
        gas = gas_costs.WARM_ACCESS + (
            gas_costs.WARM_ACCESS
            if opcode.metadata["address_warm"]
            else gas_costs.COLD_ACCOUNT_ACCESS
        )
        if not opcode.metadata["source_valid"]:
            return gas
        gas += gas_costs.WARM_ACCESS
        if opcode.metadata["code_changed"]:
            gas += gas_costs.ACCOUNT_WRITE
        return gas
