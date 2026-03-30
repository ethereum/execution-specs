"""
EIP-7702: Set EOA account code.

Add a new tx type that permanently sets the code for an EOA.

https://eips.ethereum.org/EIPS/eip-7702
"""

from dataclasses import replace
from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import OpcodeBase

from ....base_fork import (
    BaseFork,
    TransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts


class EIP7702(BaseFork):
    """EIP-7702 class."""

    @classmethod
    def tx_types(cls) -> List[int]:
        """Set-code type transactions are introduced."""
        return [4] + super(EIP7702, cls).tx_types()

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add gas costs for authorization operations."""
        return replace(
            super(EIP7702, cls).gas_costs(),
            GAS_AUTH_PER_EMPTY_ACCOUNT=25_000,
            REFUND_AUTH_PER_EXISTING_ACCOUNT=12_500,
        )

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Call gas cost needs to take the authorization into account.
        """
        metadata = opcode.metadata

        base_cost = super(EIP7702, cls)._calculate_call_gas(opcode, gas_costs)

        if metadata["delegated_address"] or metadata["delegated_address_warm"]:
            if metadata["delegated_address_warm"]:
                base_cost += gas_costs.GAS_WARM_ACCESS
            else:
                base_cost += gas_costs.GAS_COLD_ACCOUNT_ACCESS

        return base_cost

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Transaction intrinsic cost includes authorization list cost.
        """
        super_fn = super(EIP7702, cls).transaction_intrinsic_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                return_cost_deducted_prior_execution=(
                    return_cost_deducted_prior_execution
                ),
            )
            if authorization_list_or_count is not None:
                if isinstance(authorization_list_or_count, Sized):
                    authorization_list_or_count = len(
                        authorization_list_or_count
                    )
                intrinsic_cost += (
                    authorization_list_or_count
                    * gas_costs.GAS_AUTH_PER_EMPTY_ACCOUNT
                )

            return intrinsic_cost

        return fn
