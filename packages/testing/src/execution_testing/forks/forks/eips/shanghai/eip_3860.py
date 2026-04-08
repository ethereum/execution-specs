"""
EIP-3860: Limit and meter initcode.

Limit the maximum size of initcode to 49152 and apply extra gas cost of 2 for
every 32-byte chunk of initcode.

https://eips.ethereum.org/EIPS/eip-3860
"""

from execution_testing.vm import OpcodeBase

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP3860(BaseFork):
    """EIP-3860 class."""

    @classmethod
    def max_initcode_size(cls) -> int:
        """Initcode size is limited."""
        return 0xC000

    @classmethod
    def _calculate_create_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CREATE gas cost including initcode cost.
        """
        metadata = opcode.metadata

        base_cost = super(EIP3860, cls)._calculate_create_gas(
            opcode, gas_costs
        )

        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        init_code_gas = gas_costs.CODE_INIT_PER_WORD * init_code_words

        return base_cost + init_code_gas

    @classmethod
    def _calculate_create2_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CREATE2 gas cost including initcode cost.
        """
        metadata = opcode.metadata

        base_cost = super(EIP3860, cls)._calculate_create2_gas(
            opcode, gas_costs
        )

        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        init_code_gas = gas_costs.CODE_INIT_PER_WORD * init_code_words

        return base_cost + init_code_gas
