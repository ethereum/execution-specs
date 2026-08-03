"""
EIP-8037: State Creation Gas Cost Increase.

Harmonization, increase and separate metering of state creation gas costs to
mitigate state growth and unblock scaling.

The companion EIP-8038 state-access repricing lives in its own `EIP8038`
mixin. Because the EIP mixins are ordered by number, `EIP8037` sits
immediately above `EIP8038` in the MRO, so `super().gas_costs()` here
returns the EIP-8038 schedule and this mixin folds its state-creation gas
into the shared `STORAGE_SET`, `TX_CREATE`, and `AUTH_PER_EMPTY_ACCOUNT`
totals on top of it.

https://eips.ethereum.org/EIPS/eip-8037
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
        Return gas costs with the EIP-8037 state-creation gas folded
        into the relevant totals, layered on top of the EIP-8038
        state-access repricing returned by `super().gas_costs()`.
        """
        cpsb = cls.cost_per_state_byte()
        parent = super(EIP8037, cls).gas_costs()
        new_acct = STATE_BYTES_PER_NEW_ACCOUNT * cpsb

        return replace(
            parent,
            STORAGE_SET=(
                parent.STORAGE_SET + STATE_BYTES_PER_STORAGE_SET * cpsb
            ),
            NEW_ACCOUNT=new_acct,
            AUTH_BASE=STATE_BYTES_PER_AUTH_BASE * cpsb,
            TX_CREATE=parent.TX_CREATE + new_acct,
            AUTH_PER_EMPTY_ACCOUNT=(
                parent.AUTH_PER_EMPTY_ACCOUNT
                + (STATE_BYTES_PER_NEW_ACCOUNT + STATE_BYTES_PER_AUTH_BASE)
                * cpsb
            ),
            REFUND_AUTH_PER_EXISTING_ACCOUNT=new_acct,
        )

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
                execution_gas = gas_cost_or_calculator(opcode)
            else:
                execution_gas = gas_cost_or_calculator

            return execution_gas + opcode_state_calculator(opcode)

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
            Opcodes.SELFDESTRUCT: (
                lambda op: cls._calculate_selfdestruct_state_gas(op, gas_costs)
            ),
            Opcodes.CALL: lambda op: cls._calculate_call_state_gas(
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
                execution_refund = refund_or_calculator(opcode)
            else:
                execution_refund = refund_or_calculator

            return execution_refund + state_refund

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
        Calculate the execution RETURN gas cost: the code hash gas
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
        `NEW_ACCOUNT` (if the account did not exist before).
        Before EIP-8037 this was folded into `OPCODE_CREATE_BASE`. Under
        EIP-8037 it is exposed here so that `OPCODE_CREATE_BASE` stays
        execution-only and matches the spec EVM constant.
        """
        if opcode.metadata["account_new"]:
            return gas_costs.NEW_ACCOUNT
        return 0

    @classmethod
    def _calculate_selfdestruct_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the SELFDESTRUCT state gas cost: `NEW_ACCOUNT` when a
        positive balance funds a new account. Before EIP-8037 this was
        folded into the execution SELFDESTRUCT cost; under EIP-8037 it is
        exposed here as state gas (mirroring `_calculate_create_state_gas`)
        so the execution cost matches the spec EVM
        (`OPCODE_SELFDESTRUCT_BASE` + account access + the EIP-8038
        `ACCOUNT_WRITE` surcharge).
        """
        if opcode.metadata["account_new"]:
            return gas_costs.NEW_ACCOUNT
        return 0

    @classmethod
    def _calculate_selfdestruct_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution SELFDESTRUCT gas cost. The Frontier base
        calculation folds `NEW_ACCOUNT` into the execution cost when a
        positive balance funds a new account; EIP-8038 (the mixin between
        the base and EIP-8037 in the MRO) adds only the `ACCOUNT_WRITE`
        surcharge. EIP-8037 moves that funding cost to the state-gas
        dimension (see `_calculate_selfdestruct_state_gas`), so this
        subtracts the `NEW_ACCOUNT` term back out of the inherited execution
        cost; the EIP-8038 `ACCOUNT_WRITE` surcharge stays in execution gas.
        """
        gas_cost = super()._calculate_selfdestruct_gas(opcode, gas_costs)
        if opcode.metadata["account_new"]:
            gas_cost -= gas_costs.NEW_ACCOUNT
        return gas_cost

    @classmethod
    def _calculate_call_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the CALL state gas cost: `NEW_ACCOUNT` when a value
        transfer funds a new account. Before EIP-8037 this was folded
        into the execution CALL cost (EIP-161); under EIP-8037 it is
        exposed here as state gas, mirroring
        `_calculate_selfdestruct_state_gas`.
        """
        metadata = opcode.metadata
        if "value_transfer" in metadata and metadata["value_transfer"]:
            if metadata["account_new"]:
                return gas_costs.NEW_ACCOUNT
        return 0

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate the execution CALL gas cost. The EIP-161 base
        calculation folds `NEW_ACCOUNT` into the execution cost when a
        value transfer funds a new account; EIP-8037 moves that charge
        to the state-gas dimension (see `_calculate_call_state_gas`),
        so this subtracts the `NEW_ACCOUNT` term back out of the
        inherited execution cost.
        """
        gas_cost = super()._calculate_call_gas(opcode, gas_costs)
        metadata = opcode.metadata
        if "value_transfer" in metadata and metadata["value_transfer"]:
            if metadata["account_new"]:
                gas_cost -= gas_costs.NEW_ACCOUNT
        return gas_cost
