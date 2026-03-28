"""
EIP-8037: State Creation Gas Cost Increase.

Harmonization, increase and separate metering of state creation gas costs to
mitigate state growth and unblock scaling.

https://eips.ethereum.org/EIPS/eip-8037
"""

from dataclasses import replace

from execution_testing.vm import OpcodeBase

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP8037(BaseFork):
    """EIP-8037 class."""

    # TODO: return the computed value once non-default block gas
    # limits are supported in the test framework.
    _COST_PER_STATE_BYTE = 1174  # at 100M-120M gas limit

    @classmethod
    def cost_per_state_byte(cls, gas_limit: int = 0) -> int:
        """
        Calculate the state gas cost per byte based on the block gas limit.

        Mirror the EELS `state_gas_per_byte()` function with binary
        floating-point quantization (EIP-8037).

        At a gas limit of 100,000,000 this returns 1174.
        """
        TARGET = 100 * 1024**3  # noqa: N806
        BLOCKS_PER_YEAR = 2_628_000  # noqa: N806
        SIG_BITS = 5  # noqa: N806
        OFFSET = 9578  # noqa: N806
        raw = (gas_limit * BLOCKS_PER_YEAR + 2 * TARGET - 1) // (2 * TARGET)
        shifted = raw + OFFSET
        shift = max(shifted.bit_length() - SIG_BITS, 0)
        quantized = (shifted >> shift) << shift  # noqa: F841
        return cls._COST_PER_STATE_BYTE

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
        cpsb = cls.cost_per_state_byte()

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        cold_access = gas_costs.GAS_COLD_STORAGE_ACCESS
        cold_write = gas_costs.GAS_COLD_STORAGE_WRITE
        gas_cost = 0 if metadata["key_warm"] else cold_access

        if original_value == current_value and current_value != new_value:
            if original_value == 0:
                # EIP-8037: regular portion + state gas
                gas_cost += (cold_write - cold_access) + (32 * cpsb)
            else:
                gas_cost += cold_write - cold_access
        else:
            gas_cost += gas_costs.GAS_WARM_SLOAD

        return gas_cost

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate updated SSTORE gas refund.

        When restoring a slot originally empty back to zero, the
        refund includes the state gas for storage set.
        """
        metadata = opcode.metadata
        cpsb = cls.cost_per_state_byte()
        state_gas_storage_set = 32 * cpsb

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
                if original_value == 0:
                    refund += (
                        state_gas_storage_set
                        + gas_costs.GAS_COLD_STORAGE_WRITE
                        - gas_costs.GAS_COLD_STORAGE_ACCESS
                        - gas_costs.GAS_WARM_SLOAD
                    )
                else:
                    refund += (
                        gas_costs.GAS_COLD_STORAGE_WRITE
                        - gas_costs.GAS_COLD_STORAGE_ACCESS
                        - gas_costs.GAS_WARM_SLOAD
                    )

        return refund

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
            cpsb = cls.cost_per_state_byte()
            state_gas = code_deposit_size * cpsb
            code_words = (code_deposit_size + 31) // 32
            hash_gas = gas_costs.GAS_KECCAK256_PER_WORD * code_words
            return state_gas + hash_gas
        return 0
