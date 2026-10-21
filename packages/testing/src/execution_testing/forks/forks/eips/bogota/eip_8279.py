"""
EIP-8279: Block Access List Byte Floor.

Meter the bytes each opcode adds to the EIP-7928 block access list at
runtime and fold them, at the floor rate, into the transaction floor.
The bytes each EIP-7702 authorization adds enter the floor statically.

https://eips.ethereum.org/EIPS/eip-8279
"""

from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from .....recipient_type import RecipientType
from ....base_fork import BaseFork, TransactionDataFloorCostCalculator
from ...helpers import count_or_len

BAL_BYTES_PER_ADDRESS = 20
BAL_BYTES_PER_STORAGE_KEY = 32
BAL_BYTES_PER_STORAGE_VALUE = 32
BAL_BYTES_PER_BALANCE = 32
BAL_BYTES_PER_NONCE = 8
DELEGATION_CODE_BYTES = 23
AUTH_BAL_BYTES = (
    BAL_BYTES_PER_ADDRESS + DELEGATION_CODE_BYTES + BAL_BYTES_PER_NONCE
)


class EIP8279(BaseFork):
    """EIP-8279 class."""

    @classmethod
    def block_access_list_floor_cost(
        cls,
        *,
        addresses: int = 0,
        storage_keys: int = 0,
        storage_values: int = 0,
        balances: int = 0,
        nonces: int = 0,
        code_bytes: int = 0,
    ) -> int:
        """
        Return the floor gas the given block access list entries add when
        an execution meters them: their bytes at the per-byte floor rate.
        """
        bal_bytes = (
            addresses * BAL_BYTES_PER_ADDRESS
            + storage_keys * BAL_BYTES_PER_STORAGE_KEY
            + storage_values * BAL_BYTES_PER_STORAGE_VALUE
            + balances * BAL_BYTES_PER_BALANCE
            + nonces * BAL_BYTES_PER_NONCE
            + code_bytes
        )
        return bal_bytes * cls.gas_costs().FLOOR_PER_BYTE

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Add each authorization's block access list bytes -- the
        authority's address, delegation code, and nonce -- to the
        inherited floor at the per-byte floor rate.

        The term is static: it is charged whether or not the
        authorization is applied, so the bytes an applied one adds are
        always covered without metering them at runtime.
        """
        super_fn = super(EIP8279, cls).transaction_data_floor_cost_calculator()
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
            return super_fn(
                data=data,
                access_list=access_list,
                contract_creation=contract_creation,
                sends_value=sends_value,
                recipient_type=recipient_type,
                authorization_list_or_count=authorization_list_or_count,
                blob_versioned_hashes_or_count=blob_versioned_hashes_or_count,
            ) + (
                count_or_len(authorization_list_or_count)
                * AUTH_BAL_BYTES
                * gas_costs.FLOOR_PER_BYTE
            )

        return fn
