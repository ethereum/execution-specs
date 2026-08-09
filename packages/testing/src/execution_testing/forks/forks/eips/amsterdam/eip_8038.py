"""
EIP-8038: State Access Gas Cost Increase.

Harmonization and increase of state-access gas costs, repricing warm and
cold account and storage access, account writes, and the related access
list and authorization costs.

This mixin ships alongside EIP-8037 in Amsterdam. It carries the
state-access repricing only; the EIP-8037 state-creation gas is folded in
on top by the (lower-numbered, therefore shallower) `EIP8037` mixin, which
reads these values via `super().gas_costs()` and adds its state-byte
portions to the shared `STORAGE_SET`, `TX_CREATE`, and
`AUTH_PER_EMPTY_ACCOUNT` totals.

https://eips.ethereum.org/EIPS/eip-8038
"""

from dataclasses import replace
from typing import Callable, Dict

from execution_testing.vm import (
    OpcodeBase,
    Opcodes,
)

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP8038(BaseFork):
    """EIP-8038 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Return the EIP-8038 state-access gas repricing, layered on top
        of the parent fork's schedule. EIP-8037 then folds its
        state-creation gas into the relevant totals via
        `super().gas_costs()`.
        """
        parent = super(EIP8038, cls).gas_costs()

        warm_access = 100
        cold_account_access = 3_000
        cold_storage_access = 2_100
        storage_write = 10_000
        # The framework models the SSTORE write via the compound
        # COLD_STORAGE_WRITE (access + write), so preserve the invariant
        # COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS == STORAGE_WRITE.
        cold_storage_write = cold_storage_access + storage_write
        # Surcharge for the first write to an account leaf, introduced as a
        # standalone parameter by this repricing.
        account_write = 9_000
        create_access = account_write + cold_account_access
        # ecRecover stays PRECOMPILE_ECRECOVER (3000) until EIP-7904 lands.
        execution_per_auth_base_cost = (
            1_616 + 3_000 + cold_account_access + 2 * warm_access
        )

        return replace(
            parent,
            WARM_ACCESS=warm_access,
            WARM_SLOAD=warm_access,
            COLD_ACCOUNT_ACCESS=cold_account_access,
            COLD_STORAGE_ACCESS=cold_storage_access,
            COLD_STORAGE_WRITE=cold_storage_write,
            ACCOUNT_WRITE=account_write,
            CALL_VALUE=account_write + 2_300,  # ACCOUNT_WRITE + CALL_STIPEND
            REFUND_STORAGE_CLEAR=11_616,
            TX_ACCESS_LIST_ADDRESS=cold_account_access - warm_access,
            TX_ACCESS_LIST_STORAGE_KEY=cold_storage_access - warm_access,
            BLOCK_ACCESS_LIST_ITEM=2000,
            STORAGE_SET=storage_write,
            OPCODE_CREATE_BASE=create_access,
            TX_CREATE=create_access,
            AUTH_PER_EMPTY_ACCOUNT=account_write
            + execution_per_auth_base_cost,
            EXECUTION_PER_AUTH_BASE_COST=execution_per_auth_base_cost,
        )

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return the opcode gas map with the EIP-8038 `EXT*` update:
        `EXTCODESIZE` and `EXTCODECOPY` charge an extra `WARM_ACCESS`
        for the second database read (the code).
        """
        gas_costs = cls.gas_costs()
        opcode_gas_map = dict(super(EIP8038, cls).opcode_gas_map())

        def with_extra_warm_access(
            inner: int | Callable[[OpcodeBase], int],
        ) -> Callable[[OpcodeBase], int]:
            def fn(opcode: OpcodeBase) -> int:
                inner_gas = inner(opcode) if callable(inner) else inner
                return inner_gas + gas_costs.WARM_ACCESS

            return fn

        for opcode in (Opcodes.EXTCODESIZE, Opcodes.EXTCODECOPY):
            opcode_gas_map[opcode] = with_extra_warm_access(
                opcode_gas_map[opcode]
            )
        return opcode_gas_map

    @classmethod
    def _calculate_selfdestruct_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution SELFDESTRUCT gas cost. EIP-8038 adds
        `ACCOUNT_WRITE` when a positive balance is sent to an empty
        account, on top of the inherited cost (where `NEW_ACCOUNT`
        holds the EIP-8037 state-gas portion).
        """
        gas_cost = super(EIP8038, cls)._calculate_selfdestruct_gas(
            opcode, gas_costs
        )
        if opcode.metadata["account_new"]:
            gas_cost += gas_costs.ACCOUNT_WRITE
        return gas_cost

    @classmethod
    def _calculate_sstore_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution SSTORE gas cost. The state portion is
        returned separately by `_calculate_sstore_state_gas`. Under
        EIP-8038 the access cost (`COLD_STORAGE_ACCESS` when cold, else
        `WARM_SLOAD`) is always charged, and a first-time change to the
        slot additionally charges the write cost `STORAGE_WRITE`
        (modeled as `COLD_STORAGE_WRITE` minus `COLD_STORAGE_ACCESS`).
        """
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        gas_cost = (
            gas_costs.WARM_SLOAD
            if metadata["key_warm"]
            else gas_costs.COLD_STORAGE_ACCESS
        )

        if original_value == current_value and current_value != new_value:
            gas_cost += (
                gas_costs.COLD_STORAGE_WRITE - gas_costs.COLD_STORAGE_ACCESS
            )

        return gas_cost

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution SSTORE gas refund. The state portion is
        returned separately by `_calculate_sstore_state_refund`.
        """
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        refund = 0
        if current_value != new_value:
            if original_value != 0 and current_value != 0 and new_value == 0:
                refund += gas_costs.REFUND_STORAGE_CLEAR

            if original_value != 0 and current_value == 0:
                refund -= gas_costs.REFUND_STORAGE_CLEAR

            if original_value == new_value:
                # Refund the STORAGE_WRITE charged on the first-time
                # change earlier in the transaction.
                refund += (
                    gas_costs.COLD_STORAGE_WRITE
                    - gas_costs.COLD_STORAGE_ACCESS
                )

        return refund
