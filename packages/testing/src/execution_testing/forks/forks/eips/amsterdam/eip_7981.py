"""
EIP-7981: Increase Access List Cost.

Price access lists for data to reduce maximum block size.

https://eips.ethereum.org/EIPS/eip-7981
"""

from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from ....base_fork import (
    BaseFork,
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)


class EIP7981(BaseFork):
    """EIP-7981 class."""

    @classmethod
    def _access_list_floor_tokens(
        cls, access_list: List[AccessList] | None
    ) -> int:
        """
        Return ``access_list_bytes * 4`` floor tokens for the access list.

        Every byte of each address (20 bytes) and storage key (32 bytes)
        contributes four floor tokens, so zero and non-zero bytes are
        charged equally per EIP-7981.
        """
        if not access_list:
            return 0
        total_bytes = 0
        for access in access_list:
            total_bytes += len(access.address)
            for slot in access.storage_keys:
                total_bytes += len(slot)
        return total_bytes * 4

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Add access list floor tokens to the inherited calldata floor cost.
        """
        super_fn = super(EIP7981, cls).transaction_data_floor_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
        ) -> int:
            return (
                super_fn(data=data)
                + cls._access_list_floor_tokens(access_list)
                * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
            )

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Charge access list data at the floor token cost on top of the
        inherited intrinsic cost and enforce the combined data floor.
        """
        super_fn = super(EIP7981, cls).transaction_intrinsic_cost_calculator()
        gas_costs = cls.gas_costs()
        data_floor_cost_calculator = (
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
                return_cost_deducted_prior_execution=True,
            )
            intrinsic_cost += (
                cls._access_list_floor_tokens(access_list)
                * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
            )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            return max(
                intrinsic_cost,
                data_floor_cost_calculator(
                    data=calldata, access_list=access_list
                ),
            )

        return fn
