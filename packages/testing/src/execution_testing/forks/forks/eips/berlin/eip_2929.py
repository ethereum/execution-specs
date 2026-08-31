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
    def _calculate_sstore_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Charge SSTORE by net gas metering with warm and cold keys."""
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        gas_cost = 0 if metadata["key_warm"] else gas_costs.COLD_STORAGE_ACCESS

        if original_value == current_value and current_value != new_value:
            if original_value == 0:
                gas_cost += gas_costs.STORAGE_SET
            else:
                gas_cost += (
                    gas_costs.COLD_STORAGE_WRITE
                    - gas_costs.COLD_STORAGE_ACCESS
                )
        else:
            gas_cost += gas_costs.WARM_SLOAD

        return gas_cost

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Refund SSTORE by net gas metering with warm and cold keys."""
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        refund = 0
        if current_value != new_value:
            if original_value != 0 and current_value != 0 and new_value == 0:
                # Storage is cleared for the first time in the transaction
                refund += gas_costs.REFUND_STORAGE_CLEAR

            if original_value != 0 and current_value == 0:
                # Gas refund issued earlier to be reversed
                refund -= gas_costs.REFUND_STORAGE_CLEAR

            if original_value == new_value:
                # Storage slot being restored to its original value
                if original_value == 0:
                    # Slot was originally empty and was SET earlier
                    refund += gas_costs.STORAGE_SET - gas_costs.WARM_SLOAD
                else:
                    # Slot was originally non-empty and was UPDATED earlier
                    refund += (
                        gas_costs.COLD_STORAGE_WRITE
                        - gas_costs.COLD_STORAGE_ACCESS
                        - gas_costs.WARM_SLOAD
                    )

        return refund

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
