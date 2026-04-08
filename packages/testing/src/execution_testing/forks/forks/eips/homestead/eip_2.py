"""
EIP-2: Homestead Hard-fork Changes.

https://eips.ethereum.org/EIPS/eip-2
"""

from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from ....base_fork import BaseFork, TransactionIntrinsicCostCalculator


class EIP2(BaseFork):
    """EIP-2 class."""

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        The transaction intrinsic cost needs to take contract creation into
        account.
        """
        super_fn = super(EIP2, cls).transaction_intrinsic_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            del return_cost_deducted_prior_execution

            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
            )
            if contract_creation:
                intrinsic_cost += gas_costs.TX_CREATE
            return intrinsic_cost

        return fn
