"""
EIP-2930: Optional access lists.

Add a transaction type which contains an access list, a list of addresses
and storage keys that the transaction plans to access.

https://eips.ethereum.org/EIPS/eip-2930
"""

from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from ....base_fork import BaseFork, TransactionIntrinsicCostCalculator


class EIP2930(BaseFork):
    """EIP-2930 class."""

    @classmethod
    def tx_types(cls) -> List[int]:
        """Access list transactions are introduced."""
        return [1] + super(EIP2930, cls).tx_types()

    @classmethod
    def contract_creating_tx_types(cls) -> List[int]:
        """Access list transactions can create contracts."""
        return [1] + super(EIP2930, cls).contract_creating_tx_types()

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Transaction intrinsic cost includes access list cost.
        """
        super_fn = super(EIP2930, cls).transaction_intrinsic_cost_calculator()
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
                authorization_list_or_count=authorization_list_or_count,
            )
            if access_list is not None:
                for access in access_list:
                    intrinsic_cost += gas_costs.GAS_TX_ACCESS_LIST_ADDRESS
                    for _ in access.storage_keys:
                        intrinsic_cost += (
                            gas_costs.GAS_TX_ACCESS_LIST_STORAGE_KEY
                        )
            return intrinsic_cost

        return fn
