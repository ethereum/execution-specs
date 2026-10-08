"""
EIP-8131: Unified Transaction Content Floor.

Price every user-controlled transaction byte (calldata, access list
entries, EIP-7702 authorizations and blob versioned hashes) at one rate
at the floor, replacing the EIP-7976 calldata floor and the EIP-7981
access list surcharge.

https://eips.ethereum.org/EIPS/eip-8131
"""

from dataclasses import replace
from typing import List, Sized

from execution_testing.base_types import AccessList, Bytes
from execution_testing.base_types.conversions import BytesConvertible

from .....recipient_type import RecipientType
from ....base_fork import (
    BaseFork,
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts
from ...helpers import count_or_len

AUTHORIZATION_BYTES = 108
BLOB_VERSIONED_HASH_BYTES = 32


def _access_list_bytes(access_list: List[AccessList] | None) -> int:
    """Return the bytes of every address and storage key in the list."""
    if not access_list:
        return 0
    return sum(
        len(access.address) + sum(len(key) for key in access.storage_keys)
        for access in access_list
    )


class EIP8131(BaseFork):
    """EIP-8131 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Price each transaction content byte at 64 gas at the floor."""
        return replace(super(EIP8131, cls).gas_costs(), FLOOR_PER_BYTE=64)

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Charge every content byte at `FLOOR_PER_BYTE` on top of the
        intrinsic base the floor is anchored on (EIP-2780).
        """
        super_fn = super(EIP8131, cls).transaction_data_floor_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
            contract_creation: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
            authorization_list_or_count: Sized | int | None = None,
            blob_versioned_hashes_or_count: Sized | int | None = None,
        ) -> int:
            # The inherited floor of a transaction with no content is the
            # intrinsic base.
            intrinsic_base = super_fn(
                data=b"",
                contract_creation=contract_creation,
                sends_value=sends_value,
                recipient_type=recipient_type,
            )
            content_bytes = (
                len(Bytes(data))
                + _access_list_bytes(access_list)
                + count_or_len(authorization_list_or_count)
                * AUTHORIZATION_BYTES
                + count_or_len(blob_versioned_hashes_or_count)
                * BLOB_VERSIONED_HASH_BYTES
            )
            return intrinsic_base + content_bytes * gas_costs.FLOOR_PER_BYTE

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Drop the EIP-7981 access list surcharge from intrinsic gas, since
        access list bytes are now priced at the floor only, and enforce
        the content floor.
        """
        super_fn = super(EIP8131, cls).transaction_intrinsic_cost_calculator()
        floor_cost_calculator = cls.transaction_data_floor_cost_calculator()
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
            blob_versioned_hashes_or_count: Sized | int | None = None,
        ) -> int:
            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
                return_cost_deducted_prior_execution=True,
                sends_value=sends_value,
                recipient_type=recipient_type,
            )
            intrinsic_cost -= (
                _access_list_bytes(access_list)
                * 4
                * gas_costs.TX_DATA_TOKEN_FLOOR
            )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            return max(
                intrinsic_cost,
                floor_cost_calculator(
                    data=calldata,
                    access_list=access_list,
                    contract_creation=contract_creation,
                    sends_value=sends_value,
                    recipient_type=recipient_type,
                    authorization_list_or_count=authorization_list_or_count,
                    blob_versioned_hashes_or_count=blob_versioned_hashes_or_count,
                ),
            )

        return fn
