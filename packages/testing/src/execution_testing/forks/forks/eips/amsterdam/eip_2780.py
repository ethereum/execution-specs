"""
EIP-2780: Resource-based intrinsic transaction gas.

Decompose the intrinsic transaction gas into explicit recipient-access
and value-transfer primitives so that the cost paid before execution
reflects the actual work the transaction will perform.

https://eips.ethereum.org/EIPS/eip-2780
"""

from dataclasses import replace
from typing import List, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from .....recipient_type import RecipientType
from ....base_fork import (
    BaseFork,
    TopFrameGasCalculator,
    TransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts


class EIP2780(BaseFork):
    """EIP-2780 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Lower ``TX_BASE`` to 12_000 to reflect the removal of the
        bundled recipient access and account-write charges, and add
        the transfer-log and value-transfer constants.
        """
        parent = super(EIP2780, cls).gas_costs()
        return replace(
            parent,
            TX_BASE=12_000,
            TRANSFER_LOG_COST=1_756,
            TX_VALUE_COST=4_244,
        )

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Decompose intrinsic gas into explicit recipient and
        value-transfer primitives.

        Non-create, non-self targets pay ``COLD_ACCOUNT_ACCESS``
        unconditionally; access lists do not warm transaction-level
        accounts. Value-bearing transactions pay
        ``TRANSFER_LOG_COST`` plus ``TX_VALUE_COST``; self-transfers
        suppress the value-transfer charge entirely.
        """
        super_fn = super(EIP2780, cls).transaction_intrinsic_cost_calculator()
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
                return_cost_deducted_prior_execution=True,
            )

            is_self_transfer = recipient_type == RecipientType.SELF

            if contract_creation:
                if sends_value:
                    intrinsic_cost += gas_costs.TRANSFER_LOG_COST
            elif not is_self_transfer:
                intrinsic_cost += gas_costs.COLD_ACCOUNT_ACCESS
                if sends_value:
                    intrinsic_cost += (
                        gas_costs.TRANSFER_LOG_COST + gas_costs.TX_VALUE_COST
                    )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_data_floor_cost_calculator = (
                cls.transaction_data_floor_cost_calculator()
            )
            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(
                    data=calldata, access_list=access_list
                )
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn

    @classmethod
    def transaction_top_frame_gas_calculator(
        cls,
    ) -> TopFrameGasCalculator:
        """
        Return the additional regular gas charged at the top-level
        transaction frame, after intrinsic gas is deducted but before
        the EVM dispatches.

        Charges ``COLD_ACCOUNT_ACCESS`` when the recipient is an
        existing delegated account. The empty-recipient
        ``NEW_ACCOUNT`` charge is state gas, returned separately by
        ``transaction_top_frame_state_gas``.
        """
        gas_costs = cls.gas_costs()

        def fn(
            *,
            contract_creation: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            del sends_value
            if contract_creation:
                return 0

            if recipient_type == RecipientType.DELEGATION_7702:
                return gas_costs.COLD_ACCOUNT_ACCESS
            return 0

        return fn

    @classmethod
    def transaction_top_frame_state_gas(
        cls,
        *,
        contract_creation: bool = False,
        sends_value: bool = False,
        recipient_type: RecipientType = RecipientType.CONTRACT,
    ) -> int:
        """
        Return the state gas charged at the top-level transaction
        frame. Charges ``NEW_ACCOUNT`` when value is transferred to an
        empty recipient; zero otherwise. Precompile recipients are
        exempt: they are protocol-inherent rather than created by a
        value transfer, so they never trigger ``NEW_ACCOUNT`` even
        when state-empty.
        """
        gas_costs = cls.gas_costs()
        if contract_creation:
            return 0
        if recipient_type == RecipientType.PRECOMPILE:
            return 0
        if sends_value and recipient_type == RecipientType.EMPTY_ACCOUNT:
            return gas_costs.NEW_ACCOUNT
        return 0
