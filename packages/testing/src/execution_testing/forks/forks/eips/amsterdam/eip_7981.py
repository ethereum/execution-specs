"""
EIP-7981: Increase Access List Cost.

Price access lists for data to reduce maximum block size.

https://eips.ethereum.org/EIPS/eip-7981
"""

from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from .....recipient_type import RecipientType
from ....base_fork import (
    BaseFork,
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)


class EIP7981(BaseFork):
    """EIP-7981 class."""

    @classmethod
    def _access_list_data_cost(
        cls, access_list: List[AccessList] | None
    ) -> int:
        """
        Return the flat data surcharge for the access list.

        Price each address and storage key byte equally, using the
        EIP-7976 floor rate. Add this surcharge to both the intrinsic
        cost and the calldata floor, without changing the entry charges.
        """
        if not access_list:
            return 0
        total_bytes = 0
        for access in access_list:
            total_bytes += len(access.address)
            for slot in access.storage_keys:
                total_bytes += len(slot)
        return total_bytes * 4 * cls.gas_costs().TX_DATA_TOKEN_FLOOR

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Add the access list data surcharge to the inherited calldata floor.
        """
        super_fn = super(EIP7981, cls).transaction_data_floor_cost_calculator()

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
            contract_creation: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            return super_fn(
                data=data,
                contract_creation=contract_creation,
                sends_value=sends_value,
                recipient_type=recipient_type,
            ) + cls._access_list_data_cost(access_list)

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Add the access list data surcharge to the inherited intrinsic
        cost and enforce the surcharged calldata floor.
        """
        super_fn = super(EIP7981, cls).transaction_intrinsic_cost_calculator()
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
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            del sends_value, recipient_type

            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
                return_cost_deducted_prior_execution=True,
            )
            intrinsic_cost += cls._access_list_data_cost(access_list)

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            return max(
                intrinsic_cost,
                data_floor_cost_calculator(
                    data=calldata, access_list=access_list
                ),
            )

        return fn
