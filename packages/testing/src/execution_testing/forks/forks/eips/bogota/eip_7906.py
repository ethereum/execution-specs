"""
EIP-7906: Transaction Assertions via State Diff Opcode.

Add the `ASSERT` frame mode to EIP-8141 frame transactions and the
`TXTRACE` and `EVENTDATACOPY` instructions that expose the
transaction's state diff to those frames. The transaction payload and
intrinsic gas are unchanged. An `ASSERT` frame is a read-only trailing
frame whose failure reverts the execution body without invalidating the
transaction.

https://eips.ethereum.org/EIPS/eip-7906
"""

from dataclasses import replace
from typing import Callable, Dict

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts

ASSERT_MODE = 3
"""Frame mode value of an `ASSERT` assertion frame."""


class EIP7906(BaseFork):
    """EIP-7906 class."""

    @classmethod
    def frame_mode_count(cls) -> int:
        """The `ASSERT` frame mode is introduced after the existing ones."""
        count = super(EIP7906, cls).frame_mode_count()
        assert count == ASSERT_MODE, "ASSERT must be the next frame mode"
        return count + 1

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add the `TXTRACE` cost, `WARM_STORAGE_READ_COST` per EIP-7906."""
        gas_costs = super(EIP7906, cls).gas_costs()
        return replace(gas_costs, OPCODE_TXTRACE=gas_costs.WARM_ACCESS)

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Add the transaction diff instruction gas costs.

        `EVENTDATACOPY` follows `CALLDATACOPY`.
        """
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP7906, cls).opcode_gas_map()

        return {
            **base_map,
            Opcodes.TXTRACE: gas_costs.OPCODE_TXTRACE,
            Opcodes.EVENTDATACOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
        }
