"""
EIP-8037: State Creation Gas Cost Increase.

Harmonization, increase and separate metering of state creation gas costs to
mitigate state growth and unblock scaling.

This mixin also folds in the EIP-8038 state-access gas repricing: the two EIPs
ship together in Amsterdam and share one gas schedule, and the MRO places this
(highest-numbered) mixin too low to be overridden by a separate EIP-8038 mixin.
The EIP-8038 values are provisional (see the `gas_costs` override below).

https://eips.ethereum.org/EIPS/eip-8037
https://eips.ethereum.org/EIPS/eip-8038
"""

from dataclasses import replace
from typing import Callable, Dict

from execution_testing.vm import (
    OpcodeBase,
    OpcodeGasCalculator,
    Opcodes,
)

from ....base_fork import BaseFork
from ....gas_costs import GasCosts

STATE_BYTES_PER_NEW_ACCOUNT = 120
STATE_BYTES_PER_STORAGE_SET = 64
STATE_BYTES_PER_AUTH_BASE = 23

SYSTEM_MAX_SSTORES_PER_CALL = 16


class EIP8037(BaseFork):
    """EIP-8037 class."""

    @classmethod
    def cost_per_state_byte(cls) -> int:
        """
        Return the fixed cost per state byte for EIP-8037.
        """
        return 1530

    @classmethod
    def state_gas_reservoir_enabled(cls) -> bool:
        """
        State gas reservoir becomes enabled.
        """
        return True

    @classmethod
    def system_call_gas_limit(cls) -> int:
        """
        Bump the inherited limit so state gas cost changes cannot
        OOG a system call.
        """
        sstore_state_gas = (
            STATE_BYTES_PER_STORAGE_SET * cls.cost_per_state_byte()
        )
        extra = sstore_state_gas * SYSTEM_MAX_SSTORES_PER_CALL
        return super(EIP8037, cls).system_call_gas_limit() + extra

    @classmethod
    def code_deposit_state_gas(cls, *, code_size: int) -> int:
        """Return state gas for code deposit (EIP-8037)."""
        return code_size * cls.cost_per_state_byte()

    @classmethod
    def create_state_gas(cls, *, code_size: int = 0) -> int:
        """Return total state gas for CREATE (EIP-8037)."""
        gas_costs = cls.gas_costs()
        return gas_costs.NEW_ACCOUNT + cls.code_deposit_state_gas(
            code_size=code_size
        )

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Return gas costs for Amsterdam's combined EIP-8037 (state
        creation) and EIP-8038 (state access) repricing, with state gas
        folded into the relevant totals. EIP-8038 values are provisional.
        """
        cpsb = cls.cost_per_state_byte()
        parent = super(EIP8037, cls).gas_costs()
        new_acct = STATE_BYTES_PER_NEW_ACCOUNT * cpsb

        # EIP-8038 state-access repricing (provisional values).
        warm_access = 300
        cold_account_access = 7_800
        cold_storage_access = 6_300
        storage_write = 8_400
        # The framework models the SSTORE write via the compound
        # COLD_STORAGE_WRITE (access + write), so preserve the invariant
        # COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS == STORAGE_WRITE.
        cold_storage_write = cold_storage_access + storage_write
        account_write = 20_100
        create_access = 21_000
        # ecRecover stays PRECOMPILE_ECRECOVER (3000) until EIP-7904 lands.
        regular_per_auth_base_cost = (
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
            REFUND_STORAGE_CLEAR=14_400,
            TX_ACCESS_LIST_ADDRESS=7_200,
            TX_ACCESS_LIST_STORAGE_KEY=5_700,
            BLOCK_ACCESS_LIST_ITEM=2000,
            STORAGE_SET=(storage_write + STATE_BYTES_PER_STORAGE_SET * cpsb),
            NEW_ACCOUNT=new_acct,
            OPCODE_CREATE_BASE=create_access,
            TX_CREATE=(create_access + new_acct),
            AUTH_PER_EMPTY_ACCOUNT=(
                account_write
                + regular_per_auth_base_cost
                + (STATE_BYTES_PER_NEW_ACCOUNT + STATE_BYTES_PER_AUTH_BASE)
                * cpsb
            ),
            REFUND_AUTH_PER_EXISTING_ACCOUNT=new_acct,
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
        opcode_gas_map = dict(super(EIP8037, cls).opcode_gas_map())

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
        Calculate the regular SELFDESTRUCT gas cost. EIP-8038 adds
        `ACCOUNT_WRITE` when a positive balance is sent to an empty
        account, on top of the inherited cost (where `NEW_ACCOUNT`
        holds the EIP-8037 state-gas portion).
        """
        gas_cost = super(EIP8037, cls)._calculate_selfdestruct_gas(
            opcode, gas_costs
        )
        if opcode.metadata["account_new"]:
            gas_cost += gas_costs.ACCOUNT_WRITE
        return gas_cost

    @classmethod
    def opcode_gas_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas cost of a single opcode.
        """
        opcode_gas_map = cls.opcode_gas_map()
        opcode_state_calculator = cls.opcode_state_calculator()

        def fn(opcode: OpcodeBase) -> int:
            if opcode not in opcode_gas_map:
                raise ValueError(
                    f"No gas cost defined for opcode: {opcode._name_}"
                )
            gas_cost_or_calculator = opcode_gas_map[opcode]

            if callable(gas_cost_or_calculator):
                regular_gas = gas_cost_or_calculator(opcode)
            else:
                regular_gas = gas_cost_or_calculator

            return regular_gas + opcode_state_calculator(opcode)

        return fn

    @classmethod
    def opcode_state_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their state gas costs.
        """
        gas_costs = cls.gas_costs()
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_state_gas(
                op, gas_costs
            ),
            Opcodes.RETURN: lambda op: cls._calculate_return_state_gas(
                op, gas_costs
            ),
            Opcodes.CREATE: lambda op: cls._calculate_create_state_gas(
                op, gas_costs
            ),
            Opcodes.CREATE2: lambda op: cls._calculate_create_state_gas(
                op, gas_costs
            ),
        }

    @classmethod
    def opcode_state_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the state gas of a single opcode.
        """
        opcode_state_map = cls.opcode_state_map()

        def fn(opcode: OpcodeBase) -> int:
            if opcode not in opcode_state_map:
                return 0
            state_or_calculator = opcode_state_map[opcode]

            if callable(state_or_calculator):
                return state_or_calculator(opcode)

            return state_or_calculator * cls.cost_per_state_byte()

        return fn

    @classmethod
    def opcode_refund_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas refund of a single opcode.
        """
        opcode_refund_map = cls.opcode_refund_map()
        opcode_state_refund_calculator = cls.opcode_state_refund_calculator()

        def fn(opcode: OpcodeBase) -> int:
            state_refund = opcode_state_refund_calculator(opcode)
            if opcode not in opcode_refund_map:
                return state_refund
            refund_or_calculator = opcode_refund_map[opcode]

            if callable(refund_or_calculator):
                regular_refund = refund_or_calculator(opcode)
            else:
                regular_refund = refund_or_calculator

            return regular_refund + state_refund

        return fn

    @classmethod
    def opcode_state_refund_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their state refunds.
        """
        gas_costs = cls.gas_costs()
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_state_refund(
                op, gas_costs
            ),
            Opcodes.SELFDESTRUCT: (
                lambda op: cls._calculate_selfdestruct_state_refund(
                    op, gas_costs
                )
            ),
        }

    @classmethod
    def opcode_state_refund_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the state refund of a single opcode.
        """
        opcode_state_refund_map = cls.opcode_state_refund_map()

        def fn(opcode: OpcodeBase) -> int:
            if opcode not in opcode_state_refund_map:
                return 0
            state_refund_or_calculator = opcode_state_refund_map[opcode]

            if callable(state_refund_or_calculator):
                return state_refund_or_calculator(opcode)

            return state_refund_or_calculator * cls.cost_per_state_byte()

        return fn

    @classmethod
    def transaction_intrinsic_state_gas(
        cls,
        *,
        contract_creation: bool = False,
        authorization_count: int = 0,
    ) -> int:
        """
        Return the intrinsic state gas for a transaction. Creation
        adds `STATE_BYTES_PER_NEW_ACCOUNT * cpsb`, and each
        authorization adds
        `(STATE_BYTES_PER_NEW_ACCOUNT + STATE_BYTES_PER_AUTH_BASE) * cpsb`.
        """
        cpsb = cls.cost_per_state_byte()
        state_gas = 0
        if contract_creation:
            state_gas += STATE_BYTES_PER_NEW_ACCOUNT * cpsb
        state_gas += (
            (STATE_BYTES_PER_NEW_ACCOUNT + STATE_BYTES_PER_AUTH_BASE)
            * cpsb
            * authorization_count
        )
        return state_gas

    @classmethod
    def _calculate_sstore_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the regular SSTORE gas cost. The state portion is
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
    def _calculate_sstore_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the SSTORE state gas cost. Return
        `STATE_BYTES_PER_STORAGE_SET * cpsb` when a slot is first set
        from zero, otherwise return 0.
        """
        del gas_costs
        metadata = opcode.metadata
        cpsb = cls.cost_per_state_byte()

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        if (
            original_value == current_value
            and current_value != new_value
            and original_value == 0
        ):
            return STATE_BYTES_PER_STORAGE_SET * cpsb
        return 0

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the regular SSTORE gas refund. The state portion is
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

    @classmethod
    def _calculate_sstore_state_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the SSTORE state gas refund. Return
        `STATE_BYTES_PER_STORAGE_SET * cpsb` when a slot that was
        originally empty is restored back to zero within the
        transaction, otherwise return 0.
        """
        del gas_costs
        metadata = opcode.metadata
        cpsb = cls.cost_per_state_byte()

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]
        if current_value != new_value:
            if original_value == new_value:
                if original_value == 0:
                    return STATE_BYTES_PER_STORAGE_SET * cpsb
        return 0

    @classmethod
    def _calculate_selfdestruct_state_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the SELFDESTRUCT state gas refund. Refund
        `STATE_BYTES_PER_NEW_ACCOUNT * cpsb` for the destroyed account,
        `STATE_BYTES_PER_STORAGE_SET * cpsb` for each populated storage
        slot, and `cpsb` per byte of deposited code.
        """
        del gas_costs
        metadata = opcode.metadata
        cpsb = cls.cost_per_state_byte()

        self_destructed_account = metadata["self_destructed_account"]
        self_destructed_account_storage_slot_count = metadata[
            "self_destructed_account_storage_slot_count"
        ]
        self_destructed_account_code_deposit = metadata[
            "self_destructed_account_code_deposit"
        ]
        state_refund = 0
        if self_destructed_account:
            state_refund = STATE_BYTES_PER_NEW_ACCOUNT * cpsb
            state_refund += (
                STATE_BYTES_PER_STORAGE_SET
                * cpsb
                * self_destructed_account_storage_slot_count
            )
            state_refund += cpsb * self_destructed_account_code_deposit
        return state_refund

    @classmethod
    def _calculate_return_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the regular RETURN gas cost: the code hash gas
        (keccak256 of the deployed bytecode). The per byte code deposit
        cost moves to state gas, returned by `_calculate_return_state_gas`.
        """
        metadata = opcode.metadata
        code_deposit_size = metadata["code_deposit_size"]
        if code_deposit_size > 0:
            code_words = (code_deposit_size + 31) // 32
            hash_gas = gas_costs.OPCODE_KECCAK256_PER_WORD * code_words
            return hash_gas
        return 0

    @classmethod
    def _calculate_return_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the RETURN state gas cost: `cpsb` per deposited code
        byte, the state portion replacing the per byte code deposit
        cost. The code hash gas is accounted for separately in
        `_calculate_return_gas`.
        """
        del gas_costs
        metadata = opcode.metadata
        code_deposit_size = metadata["code_deposit_size"]
        if code_deposit_size > 0:
            return code_deposit_size * cls.cost_per_state_byte()
        return 0

    @classmethod
    def _calculate_create_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the CREATE and CREATE2 state gas cost, which is
        `NEW_ACCOUNT`. Before EIP-8037 this was folded into
        `OPCODE_CREATE_BASE`. Under EIP-8037 it is exposed here so that
        `OPCODE_CREATE_BASE` stays regular only and matches the spec
        EVM constant.
        """
        del opcode
        return gas_costs.NEW_ACCOUNT
