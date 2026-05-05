"""
EIP-2780: Reduce intrinsic transaction gas costs.

Reduce the base intrinsic cost of a transaction and move account access
and state update costs into explicit, recipient-dependent gas components.

https://eips.ethereum.org/EIPS/eip-2780
"""

from dataclasses import replace
from typing import Callable, List, Optional, Sized

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import OpcodeBase, Opcodes

from .....recipient_type import RecipientType
from ....base_fork import (
    BaseFork,
    TransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts


class EIP2780(BaseFork):
    """EIP-2780 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Reduce the base transaction cost and add split cold access and
        state update gas components.
        """
        return replace(
            super(EIP2780, cls).gas_costs(),
            TX_BASE=4_500,
            COLD_ACCOUNT_COST_CODE=2_600,
            COLD_ACCOUNT_COST_NO_CODE=500,
            STATE_UPDATE=1_000,
            TRANSFER_LOG_COST=1_756,
        )

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        The transaction intrinsic cost needs to take the recipient costs
        into account.
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
            recipient_is_warm: bool = False,
            recipient_delegation_is_warm: Optional[bool] = None,
        ) -> int:
            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
                return_cost_deducted_prior_execution=True,
            )

            assert (
                recipient_delegation_is_warm is None
                or recipient_type == RecipientType.DELEGATION_7702
            ), (
                "recipient_delegation_is_warm requires"
                " RecipientType.DELEGATION_7702"
            )

            log_cost = 0
            if contract_creation or recipient_type == RecipientType.SELF:
                access_cost = 0
                update_cost = 0
            elif recipient_type == RecipientType.PRECOMPILE:
                access_cost = 0
                update_cost = 0
                if sends_value:
                    update_cost += gas_costs.STATE_UPDATE
                    log_cost = gas_costs.TRANSFER_LOG_COST
            else:
                if recipient_is_warm:
                    access_cost = gas_costs.WARM_ACCESS
                elif recipient_type in (
                    RecipientType.CONTRACT,
                    RecipientType.DELEGATION_7702,
                ):
                    access_cost = gas_costs.COLD_ACCOUNT_COST_CODE
                else:
                    access_cost = gas_costs.COLD_ACCOUNT_COST_NO_CODE

                if recipient_type == RecipientType.DELEGATION_7702:
                    if recipient_delegation_is_warm:
                        access_cost += gas_costs.WARM_ACCESS
                    else:
                        access_cost += gas_costs.COLD_ACCOUNT_COST_CODE

                update_cost = 0
                if sends_value:
                    if recipient_type == RecipientType.EMPTY_ACCOUNT:
                        update_cost = gas_costs.NEW_ACCOUNT
                    else:
                        update_cost = gas_costs.STATE_UPDATE
                    log_cost = gas_costs.TRANSFER_LOG_COST

            intrinsic_cost += access_cost + update_cost + log_cost

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_data_floor_cost_calculator = (
                cls.transaction_data_floor_cost_calculator()
            )
            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(data=calldata)
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Call gas cost uses split cold access costs and restructured value
        transfer costs.

        Cold access is split into:
        - ``COLD_ACCOUNT_COST_NO_CODE`` (500) for targets without code
        - ``COLD_ACCOUNT_COST_CODE`` (2600) for targets with code

        Value transfer replaces ``CALL_VALUE`` (9000) with:
        - ``STATE_UPDATE`` (1000) for self-calls (``caller == to``); no
          ``TRANSFER_LOG_COST`` applies since EIP-7708 does not emit a log
          for self-transfers. ``CALLCODE`` is always a self-call because
          it runs target code in the caller's own context.
        - ``2 * STATE_UPDATE + TRANSFER_LOG_COST`` (3756) for existing
          non-self targets.
        - ``STATE_UPDATE + NEW_ACCOUNT + TRANSFER_LOG_COST`` (27756) for
          empty non-self targets.

        Self-call scenarios for ``CALL`` are indicated by the
        ``self_call`` metadata flag; it defaults to ``False`` so existing
        non-self tests remain unaffected.
        """
        metadata = opcode.metadata

        if metadata["address_warm"]:
            access_cost = gas_costs.WARM_ACCESS
        elif metadata.get("address_has_code", True):
            access_cost = gas_costs.COLD_ACCOUNT_COST_CODE
        else:
            access_cost = gas_costs.COLD_ACCOUNT_COST_NO_CODE

        value_cost = 0
        if "value_transfer" in metadata and metadata["value_transfer"]:
            is_self_call = opcode == Opcodes.CALLCODE or metadata.get(
                "self_call", False
            )
            if is_self_call:
                value_cost = gas_costs.STATE_UPDATE
            elif metadata["account_new"]:
                value_cost = (
                    gas_costs.STATE_UPDATE
                    + gas_costs.NEW_ACCOUNT
                    + gas_costs.TRANSFER_LOG_COST
                )
            else:
                value_cost = (
                    2 * gas_costs.STATE_UPDATE + gas_costs.TRANSFER_LOG_COST
                )

        delegation_cost = 0
        if metadata["delegated_address"] or metadata["delegated_address_warm"]:
            if metadata["delegated_address_warm"]:
                delegation_cost = gas_costs.WARM_ACCESS
            else:
                delegation_cost = gas_costs.COLD_ACCOUNT_COST_CODE

        return access_cost + value_cost + delegation_cost

    @classmethod
    def _calculate_selfdestruct_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        SELFDESTRUCT adds ``TRANSFER_LOG_COST`` when the destruction
        moves non-zero balance to a different beneficiary, mirroring the
        runtime rule in EIP-2780.
        """
        base_cost = super(EIP2780, cls)._calculate_selfdestruct_gas(
            opcode, gas_costs
        )

        if opcode.metadata.get("transfers_value", False):
            base_cost += gas_costs.TRANSFER_LOG_COST

        return base_cost

    @classmethod
    def _with_account_access(
        cls,
        base_gas: int | Callable[[OpcodeBase], int],
        gas_costs: GasCosts,
    ) -> Callable[[OpcodeBase], int]:
        """
        Split cold access cost by code presence.

        - ``COLD_ACCOUNT_COST_NO_CODE`` for accounts without code
        - ``COLD_ACCOUNT_COST_CODE`` for accounts with code
        """

        def wrapper(opcode: OpcodeBase) -> int:
            if callable(base_gas):
                base_cost = base_gas(opcode)
            else:
                base_cost = base_gas

            if opcode.metadata["address_warm"]:
                access_cost = gas_costs.WARM_ACCESS
            elif opcode.metadata["address_has_code"]:
                access_cost = gas_costs.COLD_ACCOUNT_COST_CODE
            else:
                access_cost = gas_costs.COLD_ACCOUNT_COST_NO_CODE

            return base_cost + access_cost

        return wrapper
