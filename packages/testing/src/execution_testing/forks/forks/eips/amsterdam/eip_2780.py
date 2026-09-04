"""
EIP-2780: Resource-based intrinsic transaction gas.

Decompose the intrinsic transaction gas into explicit recipient-access
and value-transfer primitives so that the cost paid before execution
reflects the actual work the transaction will perform.

https://eips.ethereum.org/EIPS/eip-2780
"""

from dataclasses import replace
from typing import List, Sequence, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible

from .....recipient_type import RecipientType
from ....base_fork import (
    AuthorizationGasInfo,
    BaseFork,
    RefundTypes,
    TransactionDataFloorCostCalculator,
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
            TX_VALUE_COST=6_000,
        )

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Anchor the calldata floor on the decomposed execution-gas intrinsic
        base (EIP-2780).

        The inherited floor base is ``TX_BASE`` alone; add the recipient
        access and value-transfer primitives so the floor never undercuts
        the transaction's own intrinsic base. Calldata and access-list
        floor tokens still accrue via the inherited calculator; init code
        and authorization costs do not enter the floor.
        """
        super_fn = super(EIP2780, cls).transaction_data_floor_cost_calculator()
        gas_costs = cls.gas_costs()

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
            contract_creation: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            floor = super_fn(data=data, access_list=access_list)
            is_self_transfer = recipient_type == RecipientType.SELF
            if contract_creation:
                # CREATE_ACCESS execution gas; TX_CREATE folds in the
                # NEW_ACCOUNT state gas, which the floor excludes.
                floor += gas_costs.TX_CREATE - gas_costs.NEW_ACCOUNT
            elif not is_self_transfer:
                floor += gas_costs.COLD_ACCOUNT_ACCESS
                if sends_value:
                    floor += gas_costs.TX_VALUE_COST
            return floor

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Decompose intrinsic gas into explicit recipient and
        value-transfer primitives.

        Non-create, non-self targets pay ``COLD_ACCOUNT_ACCESS``
        unconditionally; access lists do not warm transaction-level
        accounts. Value-bearing transactions pay ``TX_VALUE_COST``;
        self-transfers suppress the value-transfer charge entirely.
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
            # Only the state-independent base cost per authorization is
            # charged in the intrinsic; the state-dependent
            # account-creation and delegation-write costs are charged at
            # the top frame. Exclude the base-fork authorization cost
            # and re-add the base cost here.
            authorization_count = 0
            if authorization_list_or_count is not None:
                authorization_count = (
                    len(authorization_list_or_count)
                    if isinstance(authorization_list_or_count, Sized)
                    else authorization_list_or_count
                )

            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=None,
                return_cost_deducted_prior_execution=True,
            )
            intrinsic_cost += (
                authorization_count * gas_costs.EXECUTION_PER_AUTH_BASE_COST
            )

            is_self_transfer = recipient_type == RecipientType.SELF

            if contract_creation:
                # EIP-2780: the created account's NEW_ACCOUNT state gas
                # is charged at the top frame, not deducted in the
                # intrinsic. The base-fork intrinsic bundles it in, so
                # remove it here, mirroring value transfer to an empty
                # account whose NEW_ACCOUNT is likewise top-frame.
                intrinsic_cost -= gas_costs.NEW_ACCOUNT
            elif not is_self_transfer:
                intrinsic_cost += gas_costs.COLD_ACCOUNT_ACCESS
                if sends_value:
                    intrinsic_cost += gas_costs.TX_VALUE_COST

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_data_floor_cost_calculator = (
                cls.transaction_data_floor_cost_calculator()
            )
            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(
                    data=calldata,
                    access_list=access_list,
                    contract_creation=contract_creation,
                    sends_value=sends_value,
                    recipient_type=recipient_type,
                )
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn

    @classmethod
    def transaction_top_frame_execution_gas(
        cls,
        *,
        contract_creation: bool = False,
        sends_value: bool = False,
        recipient_type: RecipientType = RecipientType.CONTRACT,
        delegation_warm: bool = False,
        authorizations: Sequence[AuthorizationGasInfo] = (),
    ) -> int:
        """
        Return the additional execution gas charged at the top-level
        transaction frame, after intrinsic gas is deducted but before
        the EVM dispatches.

        Charges the delegation-target access when the recipient is an
        existing delegated account: ``WARM_ACCESS`` when the target is
        already warm, otherwise ``COLD_ACCOUNT_ACCESS``. Each
        authorization whose application is the transaction's first
        write to its authority's leaf (``first_write``) adds
        ``ACCOUNT_WRITE``. The state-gas portions (empty-recipient and
        per-authorization ``NEW_ACCOUNT``, plus ``AUTH_BASE``) are
        returned separately by ``transaction_top_frame_state_gas``.
        """
        gas_costs = cls.gas_costs()
        del sends_value
        if contract_creation:
            return 0

        execution = 0
        if recipient_type == RecipientType.DELEGATION_7702:
            execution += (
                gas_costs.WARM_ACCESS
                if delegation_warm
                else gas_costs.COLD_ACCOUNT_ACCESS
            )
        for auth in authorizations:
            if auth.first_write:
                execution += gas_costs.ACCOUNT_WRITE
        return execution

    @classmethod
    def transaction_top_frame_state_gas(
        cls,
        *,
        contract_creation: bool = False,
        sends_value: bool = False,
        recipient_type: RecipientType = RecipientType.CONTRACT,
        authorizations: Sequence[AuthorizationGasInfo] = (),
    ) -> int:
        """
        Return the state gas charged at the top-level transaction
        frame. A contract creation charges the created account's
        ``NEW_ACCOUNT`` here (state-dependent, no longer intrinsic),
        assuming a fresh target. Otherwise, charges ``NEW_ACCOUNT`` when
        value is transferred to an empty recipient, and each
        authorization adds ``NEW_ACCOUNT`` when its authority's account
        leaf must be created and ``AUTH_BASE`` when it writes a net-new
        delegation indicator.
        """
        gas_costs = cls.gas_costs()
        if contract_creation:
            return gas_costs.NEW_ACCOUNT
        state = 0
        if sends_value and recipient_type == RecipientType.EMPTY_ACCOUNT:
            state += gas_costs.NEW_ACCOUNT
        for auth in authorizations:
            if auth.creates_account:
                state += gas_costs.NEW_ACCOUNT
            if auth.writes_delegation:
                state += gas_costs.AUTH_BASE
        return state

    @classmethod
    def refund_types(cls) -> List[RefundTypes]:
        """
        Drop the existing-authority authorization refund.

        EIP-2780 charges each authorization's state-dependent cost at the
        top frame, keyed on the authority's pre-transaction state, with no
        refund. The Prague-era ``AUTHORIZATION_EXISTING_AUTHORITY`` refund
        therefore no longer applies.
        """
        return [
            refund
            for refund in super(EIP2780, cls).refund_types()
            if refund != RefundTypes.AUTHORIZATION_EXISTING_AUTHORITY
        ]
