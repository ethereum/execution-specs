"""
EIP-7623: Increase calldata cost.

Increase calldata cost to reduce maximum block size.

https://eips.ethereum.org/EIPS/eip-7623
"""

from dataclasses import replace
from typing import List, Sized

from execution_testing.base_types import AccessList, Bytes
from execution_testing.base_types.conversions import BytesConvertible

from ....base_fork import (
    BaseFork,
    CalldataGasCalculator,
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts


class EIP7623(BaseFork):
    """EIP-7623 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add standard and floor token costs for calldata."""
        return replace(
            super(EIP7623, cls).gas_costs(),
            TX_DATA_TOKEN_STANDARD=4,
            TX_DATA_TOKEN_FLOOR=10,
        )

    @classmethod
    def calldata_gas_calculator(cls) -> CalldataGasCalculator:
        """
        Return a callable that calculates the transaction gas cost for its
        calldata depending on its contents.
        """
        gas_costs = cls.gas_costs()

        def fn(*, data: BytesConvertible, floor: bool = False) -> int:
            raw = Bytes(data)
            num_zeros = raw.count(0)
            num_non_zeros = len(raw) - num_zeros
            tokens = num_zeros + num_non_zeros * 4
            if floor:
                return tokens * gas_costs.TX_DATA_TOKEN_FLOOR
            return tokens * gas_costs.TX_DATA_TOKEN_STANDARD

        return fn

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Transaction data floor cost is introduced.
        """
        calldata_gas_calculator = cls.calldata_gas_calculator()
        gas_costs = cls.gas_costs()

        def fn(*, data: BytesConvertible) -> int:
            return (
                calldata_gas_calculator(data=data, floor=True)
                + gas_costs.TX_BASE
            )

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Transaction intrinsic cost wraps the parent calculator with a floor
        cost.
        """
        super_fn = super(EIP7623, cls).transaction_intrinsic_cost_calculator()
        transaction_data_floor_cost_calculator = (
            cls.transaction_data_floor_cost_calculator()
        )

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
                authorization_list_or_count=authorization_list_or_count,
                return_cost_deducted_prior_execution=False,
            )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(data=calldata)
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn
