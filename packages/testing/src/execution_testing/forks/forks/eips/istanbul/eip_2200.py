"""
EIP-2200: Structured definitions for net gas metering.

Charge and refund SSTORE by the original, current and new value of the
slot. The dirty and no-op write cost is the SLOAD cost. EIP-1283
introduced the same scheme at Constantinople and was reverted before
activation, so it is not modeled.

https://eips.ethereum.org/EIPS/eip-2200
"""

from execution_testing.vm import OpcodeBase

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP2200(BaseFork):
    """EIP-2200 class."""

    @classmethod
    def _calculate_sstore_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Charge SSTORE by net gas metering."""
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        if original_value == current_value and current_value != new_value:
            if original_value == 0:
                return gas_costs.STORAGE_SET
            return gas_costs.COLD_STORAGE_WRITE

        # No-op and dirty writes charge the SLOAD cost.
        return gas_costs.OPCODE_SLOAD

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Refund SSTORE by net gas metering."""
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
                    refund += gas_costs.STORAGE_SET - gas_costs.OPCODE_SLOAD
                else:
                    # Slot was originally non-empty and was UPDATED earlier
                    refund += (
                        gas_costs.COLD_STORAGE_WRITE - gas_costs.OPCODE_SLOAD
                    )

        return refund
