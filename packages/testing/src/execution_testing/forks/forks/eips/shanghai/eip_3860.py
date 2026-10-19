"""
EIP-3860: Limit and meter initcode.

Limit the maximum size of initcode to 49152 and apply extra gas cost of 2 for
every 32-byte chunk of initcode.

https://eips.ethereum.org/EIPS/eip-3860
"""

from dataclasses import replace
from typing import List, Sized

from execution_testing.base_types import AccessList, Bytes
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import OpcodeBase

from .....recipient_type import RecipientType
from ....base_fork import BaseFork, TransactionIntrinsicCostCalculator
from ....gas_costs import GasCosts
from ...helpers import ceiling_division


class EIP3860(BaseFork):
    """EIP-3860 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Introduce the per-word initcode metering cost."""
        return replace(
            super(EIP3860, cls).gas_costs(),
            CODE_INIT_PER_WORD=2,
        )

    @classmethod
    def max_initcode_size(cls) -> int:
        """Initcode size is limited."""
        return 0xC000

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        The intrinsic cost of a creation transaction meters its init code.
        """
        super_fn = super(EIP3860, cls).transaction_intrinsic_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
                return_cost_deducted_prior_execution=(
                    return_cost_deducted_prior_execution
                ),
                sends_value=sends_value,
                recipient_type=recipient_type,
            )
            if contract_creation:
                intrinsic_cost += (
                    gas_costs.CODE_INIT_PER_WORD
                    * ceiling_division(len(Bytes(calldata)), 32)
                )
            return intrinsic_cost

        return fn

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
