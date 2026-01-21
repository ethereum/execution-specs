"""
EIP-7843: SLOTNUM opcode.

Opcode to get the current slot number.

https://eips.ethereum.org/EIPS/eip-7843
"""

from typing import Callable, Dict, List

from execution_testing.vm import (
    OpcodeBase,
    Opcodes,
)

from ....base_fork import BaseFork


class EIP7843(
    BaseFork,
    # Engine API method version bumps
    # New field `slotNumber` in ExecutionPayload
    engine_new_payload_version_bump=True,
    engine_get_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
):
    """EIP-7843 class."""

    @classmethod
    def header_slot_number_required(cls) -> bool:
        """Slot number in header required."""
        return True

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add SLOTNUM opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP7843, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.SLOTNUM: gas_costs.GAS_BASE,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add SLOTNUM opcode."""
        return [Opcodes.SLOTNUM] + super(EIP7843, cls).valid_opcodes()
