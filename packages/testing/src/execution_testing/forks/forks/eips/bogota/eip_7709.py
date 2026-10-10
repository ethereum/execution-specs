"""
EIP-7709: Read BLOCKHASH from storage and update cost.

Serve the BLOCKHASH opcode from the EIP-2935 history storage contract and
charge the cold or warm storage access cost of the slot it reads.

https://eips.ethereum.org/EIPS/eip-7709
"""

from typing import Callable, Dict

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP7709(BaseFork):
    """EIP-7709 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Add the cost of accessing the history storage slot to
        `BLOCKHASH` of an in-window block, priced by the `in_window` and
        `key_warm` metadata.
        """
        gas_costs = cls.gas_costs()

        def blockhash_cost(opcode: OpcodeBase) -> int:
            if not opcode.metadata["in_window"]:
                return gas_costs.OPCODE_BLOCKHASH
            if opcode.metadata["key_warm"]:
                return gas_costs.OPCODE_BLOCKHASH + gas_costs.WARM_SLOAD
            return gas_costs.OPCODE_BLOCKHASH + gas_costs.COLD_STORAGE_ACCESS

        return {
            **super(EIP7709, cls).opcode_gas_map(),
            Opcodes.BLOCKHASH: blockhash_cost,
        }
