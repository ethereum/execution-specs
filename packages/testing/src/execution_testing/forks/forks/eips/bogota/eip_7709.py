"""
EIP-7709: Read BLOCKHASH from Storage and Update Cost.

Update the BLOCKHASH (0x40) opcode to read and serve from the EIP-2935
system contract storage and charge the additional (cold or warm) storage
costs.

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
        """Price in-bounds BLOCKHASH lookups with warm or cold SLOAD gas."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP7709, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.BLOCKHASH: lambda op: (
                gas_costs.OPCODE_BLOCKHASH
                if not op.metadata["in_bounds"]
                else gas_costs.OPCODE_BLOCKHASH
                + (
                    gas_costs.WARM_SLOAD
                    if op.metadata["key_warm"]
                    else gas_costs.COLD_STORAGE_ACCESS
                )
            ),
        }
