"""
EIP-5920: PAY opcode.

Introduces a new opcode, `PAY` (`0xfc`), to send ether to an address without
calling any of its functions.

https://eips.ethereum.org/EIPS/eip-5920
"""

from typing import Callable, Dict, List

from execution_testing.vm import (
    OpcodeBase,
    Opcodes,
)

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP5920(BaseFork):
    """EIP-5920 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add PAY opcode execution gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP5920, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.PAY: lambda op: cls._calculate_pay_gas(op, gas_costs),
        }

    @classmethod
    def opcode_state_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add PAY opcode state gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP5920, cls).opcode_state_map()
        return {
            **base_map,
            Opcodes.PAY: lambda op: cls._calculate_pay_state_gas(
                op, gas_costs
            ),
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add PAY opcode."""
        return [Opcodes.PAY] + super(EIP5920, cls).valid_opcodes()

    @classmethod
    def _calculate_pay_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution PAY gas cost: account access cost
        (`WARM_ACCESS` when warm, else `COLD_ACCOUNT_ACCESS`) plus
        `ACCOUNT_WRITE` when transferring non-zero value.
        """
        metadata = opcode.metadata
        gas_cost = (
            gas_costs.WARM_ACCESS
            if metadata["address_warm"]
            else gas_costs.COLD_ACCOUNT_ACCESS
        )
        if metadata["value_transfer"]:
            gas_cost += gas_costs.ACCOUNT_WRITE
        return gas_cost

    @classmethod
    def _calculate_pay_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the PAY state gas cost: `NEW_ACCOUNT` when a non-zero
        value transfer funds a new account.
        """
        metadata = opcode.metadata
        if metadata["value_transfer"] and metadata["account_new"]:
            return gas_costs.NEW_ACCOUNT
        return 0
