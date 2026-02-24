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
    def _access_list_token_count(
        cls, access_list: List[AccessList] | None
    ) -> int:
        """
        Return the total number of data tokens contributed by an access list.

        Tokens are counted per EIP-7981:
        - zero byte = 1 token
        - non-zero byte = 4 tokens
        """
        if not access_list:
            return 0

        tokens = 0
        for access in access_list:
            for b in access.address:
                tokens += 1 if b == 0 else 4
            for slot in access.storage_keys:
                for b in slot:
                    tokens += 1 if b == 0 else 4
        return tokens

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Floor cost includes calldata and access list tokens.
        """
        calldata_gas_calculator = cls.calldata_gas_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
        ) -> int:
            access_list_tokens = cls._access_list_token_count(access_list)
            return (
                calldata_gas_calculator(data=data, floor=True)
                + access_list_tokens * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
                + gas_costs.GAS_TX_BASE
            )

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Access list data is charged at the floor token cost and
        contributes to the floor gas cost per EIP-7981.
        """
        super_fn = super(EIP7981, cls).transaction_intrinsic_cost_calculator()
        gas_costs = cls.gas_costs()
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
                return_cost_deducted_prior_execution=True,
            )
            access_list_tokens = cls._access_list_token_count(access_list)
            intrinsic_cost += (
                access_list_tokens * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
            )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(
                    data=calldata, access_list=access_list
                )
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn
