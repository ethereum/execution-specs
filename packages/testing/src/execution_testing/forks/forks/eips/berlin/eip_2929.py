"""
EIP-2929: Gas cost increases for state access opcodes.

Replace the flat account and storage access costs with warm and cold
pricing driven by the `address_warm` and `key_warm` opcode metadata.

https://eips.ethereum.org/EIPS/eip-2929
"""

from typing import Callable, Dict

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP2929(BaseFork):
    """EIP-2929 class."""

    @classmethod
    def _call_access_cost(cls, opcode: OpcodeBase, gas_costs: GasCosts) -> int:
        """Price the CALL family target access by warmth."""
        if opcode.metadata["address_warm"]:
            return gas_costs.WARM_ACCESS
        return gas_costs.COLD_ACCOUNT_ACCESS

    @classmethod
    def _selfdestruct_access_cost(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Charge cold beneficiary access."""
        if opcode.metadata["address_warm"]:
            return 0
        return gas_costs.COLD_ACCOUNT_ACCESS

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Price the account and storage access opcodes by warmth."""
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP2929, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.BALANCE: cls._with_account_access(0, gas_costs),
            Opcodes.EXTCODESIZE: cls._with_account_access(0, gas_costs),
            Opcodes.EXTCODECOPY: cls._with_memory_expansion(
                cls._with_data_copy(
                    cls._with_account_access(0, gas_costs),
                    gas_costs,
                ),
                memory_expansion_calculator,
            ),
            Opcodes.EXTCODEHASH: cls._with_account_access(0, gas_costs),
            Opcodes.SLOAD: lambda op: (
                gas_costs.WARM_SLOAD
                if op.metadata["key_warm"]
                else gas_costs.COLD_STORAGE_ACCESS
            ),
        }
