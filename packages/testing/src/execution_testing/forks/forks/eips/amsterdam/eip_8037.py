"""
EIP-8037: State Creation Gas Cost Increase.

Harmonization, increase and separate metering of state creation gas costs to
mitigate state growth and unblock scaling.

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


class EIP8037(BaseFork):
    """EIP-8037 class."""

    @classmethod
    def cost_per_state_byte(cls) -> int:
        """
        Calculate the state gas cost per byte based on `cls._env_gas_limit`.

        Mirror the EELS `state_gas_per_byte()` function with binary
        floating-point quantization (EIP-8037).

        At a gas limit of 100,000,000 this returns 1174.
        """
        TARGET = 100 * 1024**3  # noqa: N806
        BLOCKS_PER_YEAR = 2_628_000  # noqa: N806
        SIG_BITS = 5  # noqa: N806
        OFFSET = 9578  # noqa: N806
        gas_limit = cls._env_gas_limit
        raw = (gas_limit * BLOCKS_PER_YEAR + 2 * TARGET - 1) // (2 * TARGET)
        shifted = raw + OFFSET
        shift = max(shifted.bit_length() - SIG_BITS, 0)
        quantized = (shifted >> shift) << shift
        return max(quantized - OFFSET, 1)

    @classmethod
    def sstore_state_gas(cls) -> int:
        """Return state gas for a zero-to-nonzero SSTORE (EIP-8037)."""
        STATE_BYTES_PER_STORAGE_SET = 32  # noqa: N806
        return STATE_BYTES_PER_STORAGE_SET * cls.cost_per_state_byte()

    @classmethod
    def code_deposit_state_gas(cls, *, code_size: int) -> int:
        """Return state gas for code deposit (EIP-8037)."""
        return code_size * cls.cost_per_state_byte()

    @classmethod
    def create_state_gas(cls, *, code_size: int = 0) -> int:
        """Return total state gas for CREATE (EIP-8037)."""
        gas_costs = cls.gas_costs()
        return gas_costs.GAS_NEW_ACCOUNT + cls.code_deposit_state_gas(
            code_size=code_size
        )

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Gas costs are updated for two-dimensional gas metering.
        State gas is folded into totals.
        """
        cpsb = cls.cost_per_state_byte()
        parent = super(EIP8037, cls).gas_costs()
        # EIP-8037 state byte sizes (EELS amsterdam/vm/gas.py)
        STATE_BYTES_PER_STORAGE_SET = 32  # noqa: N806
        STATE_BYTES_PER_NEW_ACCOUNT = 112  # noqa: N806
        STATE_BYTES_PER_AUTH_BASE = 23  # noqa: N806
        # EIP-8037 regular gas base costs
        PER_AUTH_BASE_COST = 7_500  # noqa: N806
        REGULAR_GAS_CREATE = 9_000  # noqa: N806
        new_acct = STATE_BYTES_PER_NEW_ACCOUNT * cpsb
        return replace(
            parent,
            # EIP-7928: block access list item cost
            GAS_BLOCK_ACCESS_LIST_ITEM=2000,
            # EIP-8037: state gas folded into totals
            GAS_STORAGE_SET=(
                parent.GAS_COLD_STORAGE_WRITE
                - parent.GAS_COLD_STORAGE_ACCESS
                + STATE_BYTES_PER_STORAGE_SET * cpsb
            ),
            GAS_NEW_ACCOUNT=new_acct,
            GAS_CREATE=REGULAR_GAS_CREATE + new_acct,
            GAS_TX_CREATE=(REGULAR_GAS_CREATE + new_acct),
            GAS_AUTH_PER_EMPTY_ACCOUNT=(
                PER_AUTH_BASE_COST
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
            # Get the gas cost or calculator
            if opcode not in opcode_gas_map:
                raise ValueError(
                    f"No gas cost defined for opcode: {opcode._name_}"
                )
            gas_cost_or_calculator = opcode_gas_map[opcode]

            if callable(gas_cost_or_calculator):
                # If it's a callable, call it with the opcode
                regular_gas = gas_cost_or_calculator(opcode)
            else:
                # Otherwise it's a constant
                regular_gas = gas_cost_or_calculator

            # EIP-8037 adds the state gas on top of the regular gas cost.
            return regular_gas + opcode_state_calculator(opcode)

        return fn

    @classmethod
    def opcode_state_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their state gas costs.

        Each entry is either:
        - Constants (int): Multiplier of the cost_per_state_byte
        - Callables: Functions that take the opcode instance with metadata and
                     return the full state gas cost.
        """
        gas_costs = cls.gas_costs()
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_state_gas(
                op, gas_costs
            ),
            Opcodes.RETURN: lambda op: cls._calculate_return_state_gas(
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
            # Get the cpsb multiplier or state gas calculator
            if opcode not in opcode_state_map:
                # By default, an opcode does not incur in state gas cost.
                return 0
            state_or_calculator = opcode_state_map[opcode]

            # If it's a callable, call it with the opcode
            if callable(state_or_calculator):
                return state_or_calculator(opcode)

            # Otherwise it's a constant
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
            # Get the gas refund or calculator
            if opcode not in opcode_refund_map:
                # Most opcodes don't provide refunds
                return 0
            refund_or_calculator = opcode_refund_map[opcode]

            # If it's a callable, call it with the opcode
            if callable(refund_or_calculator):
                regular_refund = refund_or_calculator(opcode)
            else:
                # Otherwise it's a constant
                regular_refund = refund_or_calculator

            # EIP-8037 adds the state refund on top of the regular refund.
            return regular_refund + opcode_state_refund_calculator(opcode)

        return fn

    @classmethod
    def opcode_state_refund_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their state refunds.

        Each entry is either:
        - Constants (int): Multiplier of the cost_per_state_byte
        - Callables: Functions that take the opcode instance with metadata and
                     return the state refund
        """
        gas_costs = cls.gas_costs()
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_state_refund(
                op, gas_costs
            ),
        }

    @classmethod
    def opcode_state_refund_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the state refund of a single opcode.
        """
        opcode_state_refund_map = cls.opcode_state_refund_map()

        def fn(opcode: OpcodeBase) -> int:
            # Get the cpsb multiplier or state gas calculator
            if opcode not in opcode_state_refund_map:
                # By default, an opcode does not incur in state gas cost.
                return 0
            state_refund_or_calculator = opcode_state_refund_map[opcode]

            # If it's a callable, call it with the opcode
            if callable(state_refund_or_calculator):
                return state_refund_or_calculator(opcode)

            # Otherwise it's a constant
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
        Return the intrinsic state gas for a transaction (EIP-8037).

        State gas sources:
        - Creation: STATE_BYTES_PER_NEW_ACCOUNT * cpsb
        - Auth: (NEW_ACCOUNT + AUTH_BASE) * cpsb
        """
        cpsb = cls.cost_per_state_byte()
        STATE_BYTES_PER_NEW_ACCOUNT = 112  # noqa: N806
        STATE_BYTES_PER_AUTH_BASE = 23  # noqa: N806
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
        Calculate updated SSTORE gas cost.

        For 0->nonzero: regular (UPDATE - COLD_SLOAD) + state
        (32 * cpsb).
        For nonzero->different nonzero: regular
        (UPDATE - COLD_SLOAD).
        Otherwise: WARM_SLOAD.
        """
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        gas_cost = (
            0 if metadata["key_warm"] else gas_costs.GAS_COLD_STORAGE_ACCESS
        )

        if original_value == current_value and current_value != new_value:
            gas_cost += (
                gas_costs.GAS_COLD_STORAGE_WRITE
                - gas_costs.GAS_COLD_STORAGE_ACCESS
            )
        else:
            gas_cost += gas_costs.GAS_WARM_SLOAD

        return gas_cost

    @classmethod
    def _calculate_sstore_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate updated SSTORE state gas cost.
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
            return 32 * cpsb
        return 0

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate updated SSTORE regular gas refund. The state-gas
        portion is returned separately by
        `_calculate_sstore_state_refund`.
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
                refund += (
                    gas_costs.GAS_COLD_STORAGE_WRITE
                    - gas_costs.GAS_COLD_STORAGE_ACCESS
                    - gas_costs.GAS_WARM_SLOAD
                )

        return refund

    @classmethod
    def _calculate_sstore_state_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate SSTORE state gas refund.

        Return the state-gas portion (`32 * cpsb`) when a slot that
        was originally empty is restored back to zero within the
        transaction; otherwise return 0.
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
                    return 32 * cpsb
        return 0

    @classmethod
    def _calculate_return_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate updated RETURN gas cost.

        Replace G_CODE_DEPOSIT_BYTE with cpsb per byte for code
        deposit, and add code hash gas (keccak256 of deployed
        bytecode).
        """
        metadata = opcode.metadata
        code_deposit_size = metadata["code_deposit_size"]
        if code_deposit_size > 0:
            code_words = (code_deposit_size + 31) // 32
            hash_gas = gas_costs.GAS_KECCAK256_PER_WORD * code_words
            return hash_gas
        return 0

    @classmethod
    def _calculate_return_state_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate RETURN state gas cost.

        Return `cpsb` per deposited code byte (the state-gas portion
        replacing G_CODE_DEPOSIT_BYTE). Code hash gas is accounted
        for separately in `_calculate_return_gas`.
        """
        del gas_costs
        metadata = opcode.metadata
        code_deposit_size = metadata["code_deposit_size"]
        if code_deposit_size > 0:
            return code_deposit_size * cls.cost_per_state_byte()
        return 0
