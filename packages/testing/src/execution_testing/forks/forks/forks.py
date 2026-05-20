"""All Ethereum fork class definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Mapping, Sized

if TYPE_CHECKING:
    from execution_testing.fixtures.blockchain import FixtureHeader

from execution_testing.base_types import (
    AccessList,
    Address,
    BlobSchedule,
    Bytes,
    ZeroPaddedHexNumber,
)
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import (
    OpcodeBase,
    OpcodeGasCalculator,
    Opcodes,
)

from ..base_fork import (
    BaseFeeChangeCalculator,
    BaseFeePerGasCalculator,
    BaseFork,
    BlobGasPriceCalculator,
    CalldataGasCalculator,
    ExcessBlobGasCalculator,
    MemoryExpansionGasCalculator,
    RefundTypes,
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)
from ..gas_costs import BASE, HIGH, LOW, MID, VERY_LOW, GasCosts
from . import eips
from .eips.amsterdam import AmsterdamEIPs
from .helpers import ceiling_division


# All forks must be listed here !!! in the order they were introduced !!!
class Frontier(
    BaseFork,
    solc_name="homestead",
):
    """Frontier fork."""

    @classmethod
    def transition_tool_name(cls) -> str:
        """
        Return fork name as it's meant to be passed to the transition tool for
        execution.
        """
        if cls._transition_tool_name is not None:
            return cls._transition_tool_name
        return cls.name()

    @classmethod
    def solc_name(cls) -> str:
        """Return fork name as it's meant to be passed to the solc compiler."""
        if cls._solc_name is not None:
            return cls._solc_name
        return cls.name().lower()

    @classmethod
    def header_base_fee_required(cls) -> bool:
        """At genesis, header must not contain base fee."""
        return False

    @classmethod
    def header_prev_randao_required(cls) -> bool:
        """At genesis, header must not contain Prev Randao value."""
        return False

    @classmethod
    def header_zero_difficulty_required(cls) -> bool:
        """At genesis, header must not have difficulty zero."""
        return False

    @classmethod
    def header_withdrawals_required(cls) -> bool:
        """At genesis, header must not contain withdrawals."""
        return False

    @classmethod
    def header_excess_blob_gas_required(cls) -> bool:
        """At genesis, header must not contain excess blob gas."""
        return False

    @classmethod
    def header_blob_gas_used_required(cls) -> bool:
        """At genesis, header must not contain blob gas used."""
        return False

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Return dataclass with the defined gas costs constants for genesis.
        """
        return GasCosts(
            # Tiers
            BASE=BASE,
            VERY_LOW=VERY_LOW,
            LOW=LOW,
            MID=MID,
            HIGH=HIGH,
            # Access
            WARM_ACCESS=100,
            COLD_ACCOUNT_ACCESS=2_600,
            WARM_SLOAD=100,
            COLD_STORAGE_ACCESS=2_100,
            # Storage
            STORAGE_SET=20_000,
            COLD_STORAGE_WRITE=5_000,
            STORAGE_RESET=2_900,
            # Call
            CALL_VALUE=9_000,
            CALL_STIPEND=2_300,
            NEW_ACCOUNT=25_000,
            # Contract Creation
            CODE_DEPOSIT_PER_BYTE=200,
            CODE_INIT_PER_WORD=2,
            # Authorization
            AUTH_PER_EMPTY_ACCOUNT=0,
            # Utility
            MEMORY_PER_WORD=3,
            # Transactions
            TX_BASE=21_000,
            TX_ACCESS_LIST_ADDRESS=2_400,
            TX_ACCESS_LIST_STORAGE_KEY=1_900,
            TX_DATA_PER_ZERO=4,
            TX_DATA_PER_NON_ZERO=68,
            TX_CREATE=32_000,
            # Refunds
            REFUND_STORAGE_CLEAR=4_800,
            REFUND_AUTH_PER_EXISTING_ACCOUNT=0,
            # Precompiles
            PRECOMPILE_ECRECOVER=3_000,
            PRECOMPILE_SHA256_BASE=60,
            PRECOMPILE_SHA256_PER_WORD=12,
            PRECOMPILE_RIPEMD160_BASE=600,
            PRECOMPILE_RIPEMD160_PER_WORD=120,
            PRECOMPILE_IDENTITY_BASE=15,
            PRECOMPILE_IDENTITY_PER_WORD=3,
            # Static Opcodes
            OPCODE_ADD=VERY_LOW,
            OPCODE_SUB=VERY_LOW,
            OPCODE_MUL=LOW,
            OPCODE_DIV=LOW,
            OPCODE_SDIV=LOW,
            OPCODE_MOD=LOW,
            OPCODE_SMOD=LOW,
            OPCODE_ADDMOD=MID,
            OPCODE_MULMOD=MID,
            OPCODE_SIGNEXTEND=LOW,
            OPCODE_LT=VERY_LOW,
            OPCODE_GT=VERY_LOW,
            OPCODE_SLT=VERY_LOW,
            OPCODE_SGT=VERY_LOW,
            OPCODE_EQ=VERY_LOW,
            OPCODE_ISZERO=VERY_LOW,
            OPCODE_AND=VERY_LOW,
            OPCODE_OR=VERY_LOW,
            OPCODE_XOR=VERY_LOW,
            OPCODE_NOT=VERY_LOW,
            OPCODE_BYTE=VERY_LOW,
            OPCODE_JUMP=MID,
            OPCODE_JUMPI=HIGH,
            OPCODE_JUMPDEST=1,
            OPCODE_CALLDATALOAD=VERY_LOW,
            OPCODE_BLOCKHASH=20,
            OPCODE_COINBASE=BASE,
            OPCODE_PUSH=VERY_LOW,
            OPCODE_DUP=VERY_LOW,
            OPCODE_SWAP=VERY_LOW,
            # Dynamic Opcode Components
            OPCODE_CALLDATACOPY_BASE=VERY_LOW,
            OPCODE_CODECOPY_BASE=VERY_LOW,
            OPCODE_MLOAD_BASE=VERY_LOW,
            OPCODE_MSTORE_BASE=VERY_LOW,
            OPCODE_MSTORE8_BASE=VERY_LOW,
            OPCODE_SELFDESTRUCT_BASE=5_000,
            OPCODE_COPY_PER_WORD=3,
            OPCODE_CREATE_BASE=32_000,
            OPCODE_EXP_BASE=10,
            OPCODE_EXP_PER_BYTE=50,
            OPCODE_LOG_BASE=375,
            OPCODE_LOG_DATA_PER_BYTE=8,
            OPCODE_LOG_TOPIC=375,
            OPCODE_KECCAK256_BASE=30,
            OPCODE_KECCACK256_PER_WORD=6,
            # Zero-initialized: introduced in later forks, set via
            # replace() in the fork that activates them.
            TX_DATA_TOKEN_STANDARD=0,
            TX_DATA_TOKEN_FLOOR=0,
            PRECOMPILE_ECADD=0,
            PRECOMPILE_ECMUL=0,
            PRECOMPILE_ECPAIRING_BASE=0,
            PRECOMPILE_ECPAIRING_PER_POINT=0,
            PRECOMPILE_BLAKE2F_BASE=0,
            PRECOMPILE_BLAKE2F_PER_ROUND=0,
            PRECOMPILE_POINT_EVALUATION=0,
            PRECOMPILE_BLS_G1ADD=0,
            PRECOMPILE_BLS_G1MUL=0,
            PRECOMPILE_BLS_G1MAP=0,
            PRECOMPILE_BLS_G2ADD=0,
            PRECOMPILE_BLS_G2MUL=0,
            PRECOMPILE_BLS_G2MAP=0,
            PRECOMPILE_BLS_PAIRING_BASE=0,
            PRECOMPILE_BLS_PAIRING_PER_PAIR=0,
            PRECOMPILE_P256VERIFY=0,
            BLOCK_ACCESS_LIST_ITEM=0,
        )

    @classmethod
    def _with_memory_expansion(
        cls,
        base_gas: int | Callable[[OpcodeBase], int],
        memory_expansion_gas_calculator: MemoryExpansionGasCalculator,
    ) -> Callable[[OpcodeBase], int]:
        """
        Wrap a gas cost calculator to include memory expansion cost.

        Args:
            base_gas: Either a constant gas cost (int) or a callable that
                      calculates it
            memory_expansion_gas_calculator: Calculator for memory expansion
                                             cost

        Returns:
            A callable that calculates base_gas + memory_expansion_cost

        """

        def wrapper(opcode: OpcodeBase) -> int:
            # Calculate base gas cost
            if callable(base_gas):
                base_cost = base_gas(opcode)
            else:
                base_cost = base_gas

            # Add memory expansion cost if metadata is present
            new_memory_size = opcode.metadata["new_memory_size"]
            old_memory_size = opcode.metadata["old_memory_size"]
            expansion_cost = memory_expansion_gas_calculator(
                new_bytes=new_memory_size, previous_bytes=old_memory_size
            )

            return base_cost + expansion_cost

        return wrapper

    @classmethod
    def _with_account_access(
        cls,
        base_gas: int | Callable[[OpcodeBase], int],
        gas_costs: "GasCosts",
    ) -> Callable[[OpcodeBase], int]:
        """
        Wrap a gas cost calculator to include account access cost.

        Args:
            base_gas: Either a constant gas cost (int) or a callable that
                      calculates it
            gas_costs: The gas costs dataclass for accessing warm/cold costs

        Returns:
            A callable that calculates base_gas + account_access_cost

        """

        def wrapper(opcode: OpcodeBase) -> int:
            # Calculate base gas cost
            if callable(base_gas):
                base_cost = base_gas(opcode)
            else:
                base_cost = base_gas

            # Add account access cost based on warmth
            if opcode.metadata["address_warm"]:
                access_cost = gas_costs.WARM_ACCESS
            else:
                access_cost = gas_costs.COLD_ACCOUNT_ACCESS

            return base_cost + access_cost

        return wrapper

    @classmethod
    def _with_data_copy(
        cls,
        base_gas: int | Callable[[OpcodeBase], int],
        gas_costs: "GasCosts",
    ) -> Callable[[OpcodeBase], int]:
        """
        Wrap a gas cost calculator to include data copy cost.

        Args:
            base_gas: Either a constant gas cost (int) or a callable that
                      calculates it
            gas_costs: The gas costs dataclass for accessing
                       OPCODE_COPY_PER_WORD

        Returns:
            A callable that calculates base_gas + copy_cost

        """

        def wrapper(opcode: OpcodeBase) -> int:
            # Calculate base gas cost
            if callable(base_gas):
                base_cost = base_gas(opcode)
            else:
                base_cost = base_gas

            # Add copy cost based on data size
            data_size = opcode.metadata["data_size"]
            word_count = (data_size + 31) // 32
            copy_cost = gas_costs.OPCODE_COPY_PER_WORD * word_count

            return base_cost + copy_cost

        return wrapper

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas costs.

        Each entry is either:
        - Constants (int): Direct gas cost values from gas_costs()
        - Callables: Functions that take the opcode instance with metadata and
                     return gas cost
        """
        gas_costs = cls.gas_costs()
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()

        # Define the opcode gas cost mapping
        # Each entry is either:
        # - an int (constant cost)
        # - a callable(opcode) -> int
        return {
            # Stop and arithmetic operations
            Opcodes.STOP: 0,
            Opcodes.ADD: gas_costs.OPCODE_ADD,
            Opcodes.MUL: gas_costs.OPCODE_MUL,
            Opcodes.SUB: gas_costs.OPCODE_SUB,
            Opcodes.DIV: gas_costs.OPCODE_DIV,
            Opcodes.SDIV: gas_costs.OPCODE_SDIV,
            Opcodes.MOD: gas_costs.OPCODE_MOD,
            Opcodes.SMOD: gas_costs.OPCODE_SMOD,
            Opcodes.ADDMOD: gas_costs.OPCODE_ADDMOD,
            Opcodes.MULMOD: gas_costs.OPCODE_MULMOD,
            Opcodes.EXP: lambda op: (
                gas_costs.OPCODE_EXP_BASE
                + gas_costs.OPCODE_EXP_PER_BYTE
                * ((op.metadata["exponent"].bit_length() + 7) // 8)
            ),
            Opcodes.SIGNEXTEND: gas_costs.OPCODE_SIGNEXTEND,
            # Comparison & bitwise logic operations
            Opcodes.LT: gas_costs.OPCODE_LT,
            Opcodes.GT: gas_costs.OPCODE_GT,
            Opcodes.SLT: gas_costs.OPCODE_SLT,
            Opcodes.SGT: gas_costs.OPCODE_SGT,
            Opcodes.EQ: gas_costs.OPCODE_EQ,
            Opcodes.ISZERO: gas_costs.OPCODE_ISZERO,
            Opcodes.AND: gas_costs.OPCODE_AND,
            Opcodes.OR: gas_costs.OPCODE_OR,
            Opcodes.XOR: gas_costs.OPCODE_XOR,
            Opcodes.NOT: gas_costs.OPCODE_NOT,
            Opcodes.BYTE: gas_costs.OPCODE_BYTE,
            # SHA3
            Opcodes.SHA3: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_KECCAK256_BASE
                    + gas_costs.OPCODE_KECCACK256_PER_WORD
                    * ((op.metadata["data_size"] + 31) // 32)
                ),
                memory_expansion_calculator,
            ),
            # Environmental information
            Opcodes.ADDRESS: gas_costs.BASE,
            Opcodes.BALANCE: cls._with_account_access(0, gas_costs),
            Opcodes.ORIGIN: gas_costs.BASE,
            Opcodes.CALLER: gas_costs.BASE,
            Opcodes.CALLVALUE: gas_costs.BASE,
            Opcodes.CALLDATALOAD: gas_costs.OPCODE_CALLDATALOAD,
            Opcodes.CALLDATASIZE: gas_costs.BASE,
            Opcodes.CALLDATACOPY: cls._with_memory_expansion(
                cls._with_data_copy(
                    gas_costs.OPCODE_CALLDATACOPY_BASE, gas_costs
                ),
                memory_expansion_calculator,
            ),
            Opcodes.CODESIZE: gas_costs.BASE,
            Opcodes.CODECOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.OPCODE_CODECOPY_BASE, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.GASPRICE: gas_costs.BASE,
            Opcodes.EXTCODESIZE: cls._with_account_access(0, gas_costs),
            Opcodes.EXTCODECOPY: cls._with_memory_expansion(
                cls._with_data_copy(
                    cls._with_account_access(0, gas_costs),
                    gas_costs,
                ),
                memory_expansion_calculator,
            ),
            # Block information
            Opcodes.BLOCKHASH: gas_costs.OPCODE_BLOCKHASH,
            Opcodes.COINBASE: gas_costs.OPCODE_COINBASE,
            Opcodes.TIMESTAMP: gas_costs.BASE,
            Opcodes.NUMBER: gas_costs.BASE,
            Opcodes.PREVRANDAO: gas_costs.BASE,
            Opcodes.GASLIMIT: gas_costs.BASE,
            # Stack, memory, storage and flow operations
            Opcodes.POP: gas_costs.BASE,
            Opcodes.MLOAD: cls._with_memory_expansion(
                gas_costs.OPCODE_MLOAD_BASE,
                memory_expansion_calculator,
            ),
            Opcodes.MSTORE: cls._with_memory_expansion(
                gas_costs.OPCODE_MSTORE_BASE,
                memory_expansion_calculator,
            ),
            Opcodes.MSTORE8: cls._with_memory_expansion(
                gas_costs.OPCODE_MSTORE8_BASE,
                memory_expansion_calculator,
            ),
            Opcodes.SLOAD: lambda op: (
                gas_costs.WARM_SLOAD
                if op.metadata["key_warm"]
                else gas_costs.COLD_STORAGE_ACCESS
            ),
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_gas(
                op, gas_costs
            ),
            Opcodes.JUMP: gas_costs.OPCODE_JUMP,
            Opcodes.JUMPI: gas_costs.OPCODE_JUMPI,
            Opcodes.PC: gas_costs.BASE,
            Opcodes.MSIZE: gas_costs.BASE,
            Opcodes.GAS: gas_costs.BASE,
            Opcodes.JUMPDEST: gas_costs.OPCODE_JUMPDEST,
            # Push operations (PUSH1 through PUSH32)
            **{
                getattr(Opcodes, f"PUSH{i}"): gas_costs.OPCODE_PUSH
                for i in range(1, 33)
            },
            # Dup operations (DUP1 through DUP16)
            **{
                getattr(Opcodes, f"DUP{i}"): gas_costs.OPCODE_DUP
                for i in range(1, 17)
            },
            # Swap operations (SWAP1 through SWAP16)
            **{
                getattr(Opcodes, f"SWAP{i}"): gas_costs.OPCODE_SWAP
                for i in range(1, 17)
            },
            # Logging operations
            Opcodes.LOG0: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_LOG_BASE
                    + gas_costs.OPCODE_LOG_DATA_PER_BYTE
                    * op.metadata["data_size"]
                ),
                memory_expansion_calculator,
            ),
            Opcodes.LOG1: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_LOG_BASE
                    + gas_costs.OPCODE_LOG_DATA_PER_BYTE
                    * op.metadata["data_size"]
                    + gas_costs.OPCODE_LOG_TOPIC
                ),
                memory_expansion_calculator,
            ),
            Opcodes.LOG2: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_LOG_BASE
                    + gas_costs.OPCODE_LOG_DATA_PER_BYTE
                    * op.metadata["data_size"]
                    + gas_costs.OPCODE_LOG_TOPIC * 2
                ),
                memory_expansion_calculator,
            ),
            Opcodes.LOG3: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_LOG_BASE
                    + gas_costs.OPCODE_LOG_DATA_PER_BYTE
                    * op.metadata["data_size"]
                    + gas_costs.OPCODE_LOG_TOPIC * 3
                ),
                memory_expansion_calculator,
            ),
            Opcodes.LOG4: cls._with_memory_expansion(
                lambda op: (
                    gas_costs.OPCODE_LOG_BASE
                    + gas_costs.OPCODE_LOG_DATA_PER_BYTE
                    * op.metadata["data_size"]
                    + gas_costs.OPCODE_LOG_TOPIC * 4
                ),
                memory_expansion_calculator,
            ),
            # System operations
            Opcodes.CREATE: cls._with_memory_expansion(
                lambda op: cls._calculate_create_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.CALL: cls._with_memory_expansion(
                lambda op: cls._calculate_call_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.CALLCODE: cls._with_memory_expansion(
                lambda op: cls._calculate_call_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.RETURN: cls._with_memory_expansion(
                lambda op: cls._calculate_return_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.INVALID: 0,
            Opcodes.SELFDESTRUCT: lambda op: cls._calculate_selfdestruct_gas(
                op, gas_costs
            ),
        }

    @classmethod
    def opcode_gas_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas cost of a single opcode.
        """
        opcode_gas_map = cls.opcode_gas_map()

        def fn(opcode: OpcodeBase) -> int:
            # Get the gas cost or calculator
            if opcode not in opcode_gas_map:
                raise ValueError(
                    f"No gas cost defined for opcode: {opcode._name_}"
                )
            gas_cost_or_calculator = opcode_gas_map[opcode]

            # If it's a callable, call it with the opcode
            if callable(gas_cost_or_calculator):
                return gas_cost_or_calculator(opcode)

            # Otherwise it's a constant
            return gas_cost_or_calculator

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
        # At Frontier, state costs do not apply.
        return {}

    @classmethod
    def opcode_state_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the state gas of a single opcode.
        """

        def fn(opcode: OpcodeBase) -> int:
            del opcode
            return 0

        return fn

    @classmethod
    def opcode_refund_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas refunds.

        Each entry is either:
        - Constants (int): Direct gas refund values
        - Callables: Functions that take the opcode instance with metadata and
                     return gas refund
        """
        gas_costs = cls.gas_costs()

        # Only SSTORE provides refunds
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_refund(
                op, gas_costs
            ),
        }

    @classmethod
    def opcode_refund_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas refund of a single opcode.
        """
        opcode_refund_map = cls.opcode_refund_map()

        def fn(opcode: OpcodeBase) -> int:
            # Get the gas refund or calculator
            if opcode not in opcode_refund_map:
                # Most opcodes don't provide refunds
                return 0
            refund_or_calculator = opcode_refund_map[opcode]

            # If it's a callable, call it with the opcode
            if callable(refund_or_calculator):
                return refund_or_calculator(opcode)

            # Otherwise it's a constant
            return refund_or_calculator

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
        # At Frontier, state refunds do not apply.
        return {}

    @classmethod
    def opcode_state_refund_calculator(cls) -> OpcodeGasCalculator:
        """
        Return callable that calculates the state refund of a single opcode.
        """

        def fn(opcode: OpcodeBase) -> int:
            del opcode
            return 0

        return fn

    @classmethod
    def _calculate_sstore_refund(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate SSTORE gas refund based on metadata."""
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        # Refund is provided when setting from non-zero to zero
        refund = 0
        if current_value != new_value:
            if original_value != 0 and current_value != 0 and new_value == 0:
                # Storage is cleared for the first time in the transaction
                refund += gas_costs.REFUND_STORAGE_CLEAR

            if original_value != 0 and current_value == 0:
                # Gas refund issued earlier to be reversed
                refund -= gas_costs.REFUND_STORAGE_CLEAR

            if original_value == new_value:
                # Storage slot being restored to its original value
                if original_value == 0:
                    # Slot was originally empty and was SET earlier
                    refund += gas_costs.STORAGE_SET - gas_costs.WARM_SLOAD
                else:
                    # Slot was originally non-empty and was UPDATED earlier
                    refund += (
                        gas_costs.COLD_STORAGE_WRITE
                        - gas_costs.COLD_STORAGE_ACCESS
                        - gas_costs.WARM_SLOAD
                    )

        return refund

    @classmethod
    def _calculate_sstore_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate SSTORE gas cost based on metadata."""
        metadata = opcode.metadata

        original_value = metadata["original_value"]
        current_value = metadata["current_value"]
        if current_value is None:
            current_value = original_value
        new_value = metadata["new_value"]

        gas_cost = 0 if metadata["key_warm"] else gas_costs.COLD_STORAGE_ACCESS

        if original_value == current_value and current_value != new_value:
            if original_value == 0:
                gas_cost += gas_costs.STORAGE_SET
            else:
                gas_cost += (
                    gas_costs.COLD_STORAGE_WRITE
                    - gas_costs.COLD_STORAGE_ACCESS
                )
        else:
            gas_cost += gas_costs.WARM_SLOAD

        return gas_cost

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CALL/DELEGATECALL/STATICCALL gas cost based on metadata.
        """
        metadata = opcode.metadata

        # Base cost depends on address warmth
        if metadata["address_warm"]:
            base_cost = gas_costs.WARM_ACCESS
        else:
            base_cost = gas_costs.COLD_ACCOUNT_ACCESS

        if metadata["inner_call_cost"]:
            return base_cost + metadata["inner_call_cost"]

        return base_cost

    @classmethod
    def _calculate_create_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """CREATE gas is constant at Frontier."""
        del opcode
        return gas_costs.OPCODE_CREATE_BASE

    @classmethod
    def _calculate_create2_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CREATE2 gas cost including initcode cost.
        """
        raise NotImplementedError(
            f"CREATE2 opcode is not supported in {cls.name()}"
        )

    @classmethod
    def _calculate_return_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate RETURN gas cost based on metadata."""
        metadata = opcode.metadata

        # Code deposit cost when returning from initcode
        code_deposit_size = metadata["code_deposit_size"]
        return gas_costs.CODE_DEPOSIT_PER_BYTE * code_deposit_size

    @classmethod
    def _calculate_selfdestruct_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate SELFDESTRUCT gas cost based on metadata."""
        metadata = opcode.metadata

        base_cost = gas_costs.OPCODE_SELFDESTRUCT_BASE

        # Check if the beneficiary is cold
        if not metadata["address_warm"]:
            base_cost += gas_costs.COLD_ACCOUNT_ACCESS

        # Check if creating a new account
        if metadata["account_new"]:
            base_cost += gas_costs.NEW_ACCOUNT

        return base_cost

    @classmethod
    def memory_expansion_gas_calculator(cls) -> MemoryExpansionGasCalculator:
        """
        Return callable that calculates the gas cost of memory expansion for
        the fork.
        """
        gas_costs = cls.gas_costs()

        def fn(*, new_bytes: int, previous_bytes: int = 0) -> int:
            if new_bytes <= previous_bytes:
                return 0
            new_words = ceiling_division(new_bytes, 32)
            previous_words = ceiling_division(previous_bytes, 32)

            def c(w: int) -> int:
                return (gas_costs.MEMORY_PER_WORD * w) + ((w * w) // 512)

            return c(new_words) - c(previous_words)

        return fn

    @classmethod
    def calldata_gas_calculator(cls) -> CalldataGasCalculator:
        """
        Return callable that calculates the transaction gas cost for its
        calldata depending on its contents.
        """
        gas_costs = cls.gas_costs()

        def fn(*, data: BytesConvertible, floor: bool = False) -> int:
            del floor

            raw = Bytes(data)
            num_zeros = raw.count(0)
            num_non_zeros = len(raw) - num_zeros
            return (
                num_zeros * gas_costs.TX_DATA_PER_ZERO
                + num_non_zeros * gas_costs.TX_DATA_PER_NON_ZERO
            )

        return fn

    @classmethod
    def base_fee_per_gas_calculator(cls) -> BaseFeePerGasCalculator:
        """
        Return a callable that calculates the base fee per gas at a given fork.
        """
        raise NotImplementedError(
            f"Base fee per gas calculator is not supported in {cls.name()}"
        )

    @classmethod
    def base_fee_change_calculator(cls) -> BaseFeeChangeCalculator:
        """
        Return a callable that calculates the gas that needs to be used to
        change the base fee.
        """
        raise NotImplementedError(
            f"Base fee change calculator is not supported in {cls.name()}"
        )

    @classmethod
    def cost_per_state_byte(cls) -> int:
        """
        Calculate the state gas cost per byte based on `cls._env_gas_limit`.
        """
        return 0

    @classmethod
    def base_fee_max_change_denominator(cls) -> int:
        """Return the base fee max change denominator at a given fork."""
        raise NotImplementedError(
            f"Base fee max change denominator is not supported in {cls.name()}"
        )

    @classmethod
    def base_fee_elasticity_multiplier(cls) -> int:
        """Return the base fee elasticity multiplier at a given fork."""
        raise NotImplementedError(
            f"Base fee elasticity multiplier is not supported in {cls.name()}"
        )

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """At frontier, the transaction data floor cost is a constant zero."""

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
        ) -> int:
            del data, access_list
            return 0

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls,
    ) -> TransactionIntrinsicCostCalculator:
        """
        Return callable that calculates the intrinsic gas cost of a transaction
        for the fork.
        """
        gas_costs = cls.gas_costs()
        calldata_gas_calculator = cls.calldata_gas_calculator()

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            del return_cost_deducted_prior_execution

            assert access_list is None, (
                f"Access list is not supported in {cls.name()}"
            )
            assert authorization_list_or_count is None, (
                f"Authorizations are not supported in {cls.name()}"
            )

            intrinsic_cost: int = gas_costs.TX_BASE

            if contract_creation:
                intrinsic_cost += (
                    gas_costs.CODE_INIT_PER_WORD
                    * ceiling_division(len(Bytes(calldata)), 32)
                )

            return intrinsic_cost + calldata_gas_calculator(data=calldata)

        return fn

    @classmethod
    def blob_gas_price_calculator(cls) -> BlobGasPriceCalculator:
        """
        Return a callable that calculates the blob gas price at a given fork.
        """
        raise NotImplementedError(
            f"Blob gas price calculator is not supported in {cls.name()}"
        )

    @classmethod
    def excess_blob_gas_calculator(cls) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block at a
        given fork.
        """
        raise NotImplementedError(
            f"Excess blob gas calculator is not supported in {cls.name()}"
        )

    @classmethod
    def supports_blobs(cls) -> bool:
        """Blobs are not supported at Frontier."""
        return False

    @classmethod
    def blob_reserve_price_active(cls) -> bool:
        """
        Return whether the fork uses a reserve price mechanism for blobs or
        not.
        """
        raise NotImplementedError(
            f"Blob reserve price is not supported in {cls.name()}"
        )

    @classmethod
    def full_blob_tx_wrapper_version(cls) -> int | None:
        """Return the version of the full blob transaction wrapper."""
        raise NotImplementedError(
            "Full blob transaction wrapper version is not supported in "
            f"{cls.name()}"
        )

    @classmethod
    def blob_schedule(cls) -> BlobSchedule | None:
        """At genesis, no blob schedule is used."""
        return None

    @classmethod
    def header_requests_required(cls) -> bool:
        """At genesis, header must not contain beacon chain requests."""
        return False

    @classmethod
    def header_bal_hash_required(cls) -> bool:
        """At genesis, header must not contain block access list hash."""
        return False

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Pre-Amsterdam forks have no block access list."""
        return 0

    @classmethod
    def header_beacon_root_required(cls) -> bool:
        """At genesis, header must not contain parent beacon block root."""
        return False

    @classmethod
    def header_slot_number_required(cls) -> bool:
        """At genesis, header must not contain slot number (EIP-7843)."""
        return False

    @classmethod
    def engine_new_payload_blob_hashes(cls) -> bool:
        """At genesis, payloads do not have blob hashes."""
        return False

    @classmethod
    def engine_new_payload_beacon_root(cls) -> bool:
        """At genesis, payloads do not have a parent beacon block root."""
        return False

    @classmethod
    def engine_new_payload_requests(cls) -> bool:
        """At genesis, payloads do not have requests."""
        return False

    @classmethod
    def engine_execution_payload_block_access_list(cls) -> bool:
        """At genesis, payloads do not have block access list."""
        return False

    @classmethod
    def engine_new_payload_target_blobs_per_block(cls) -> bool:
        """At genesis, payloads do not have target blobs per block."""
        return False

    @classmethod
    def engine_payload_attribute_target_blobs_per_block(cls) -> bool:
        """
        At genesis, payload attributes do not include the target blobs per
        block.
        """
        return False

    @classmethod
    def engine_payload_attribute_max_blobs_per_block(cls) -> bool:
        """
        At genesis, payload attributes do not include the max blobs per block.
        """
        return False

    @classmethod
    def engine_payload_attribute_slot_number(cls) -> bool:
        """
        At genesis, payload attributes do not include the slot number.
        """
        return False

    @classmethod
    def get_reward(cls) -> int:
        """
        At Genesis the expected reward amount in wei is
        5_000_000_000_000_000_000.
        """
        return 5_000_000_000_000_000_000

    @classmethod
    def supports_protected_txs(cls) -> bool:
        """At Genesis, fork has no support for EIP-155 protected txs."""
        return False

    @classmethod
    def tx_types(cls) -> List[int]:
        """At Genesis, only legacy transactions are allowed."""
        return [0]

    @classmethod
    def contract_creating_tx_types(cls) -> List[int]:
        """At Genesis, only legacy transactions are allowed."""
        return [0]

    @classmethod
    def transaction_gas_limit_cap(cls) -> int | None:
        """At Genesis, no transaction gas limit cap is imposed."""
        return None

    @classmethod
    def sstore_state_gas(cls) -> int:
        """Return the state gas for a zero-to-nonzero SSTORE."""
        return 0

    @classmethod
    def code_deposit_state_gas(cls, *, code_size: int) -> int:
        """Return the state gas for code deposit of the given size."""
        del code_size
        return 0

    @classmethod
    def create_state_gas(cls, *, code_size: int = 0) -> int:
        """Return total state gas for CREATE (new account + code deposit)."""
        del code_size
        return 0

    @classmethod
    def block_rlp_size_limit(cls) -> int | None:
        """At Genesis, no RLP block size limit is imposed."""
        return None

    @classmethod
    def precompiles(cls) -> List[Address]:
        """
        At Genesis, EC-recover, SHA256, RIPEMD160, and Identity precompiles
        are introduced.
        """
        return [
            Address(1, label="ECREC"),
            Address(2, label="SHA256"),
            Address(3, label="RIPEMD160"),
            Address(4, label="ID"),
        ]

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """At Genesis, no system contracts are present."""
        return []

    @classmethod
    def deterministic_factory_predeploy_address(cls) -> Address | None:
        """At Genesis, no deterministic factory predeploy is present."""
        return None

    @classmethod
    def max_code_size(cls) -> int:
        """
        At genesis, there is no upper bound for code size (bounded by block gas
        limit).

        However, the default is set to the limit of EIP-170 (Spurious Dragon)
        """
        return 0x6000

    @classmethod
    def max_stack_height(cls) -> int:
        """At genesis, the maximum stack height is 1024."""
        return 1024

    @classmethod
    def max_initcode_size(cls) -> int:
        """
        At genesis, there is no upper bound for initcode size.

        However, the default is set to the limit of EIP-3860 (Shanghai).
        """
        return 0xC000

    @classmethod
    def call_opcodes(cls) -> List[Opcodes]:
        """Return list of call opcodes supported by the fork."""
        return [Opcodes.CALL, Opcodes.CALLCODE]

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        return [
            Opcodes.STOP,
            Opcodes.ADD,
            Opcodes.MUL,
            Opcodes.SUB,
            Opcodes.DIV,
            Opcodes.SDIV,
            Opcodes.MOD,
            Opcodes.SMOD,
            Opcodes.ADDMOD,
            Opcodes.MULMOD,
            Opcodes.EXP,
            Opcodes.SIGNEXTEND,
            Opcodes.LT,
            Opcodes.GT,
            Opcodes.SLT,
            Opcodes.SGT,
            Opcodes.EQ,
            Opcodes.ISZERO,
            Opcodes.AND,
            Opcodes.OR,
            Opcodes.XOR,
            Opcodes.NOT,
            Opcodes.BYTE,
            Opcodes.SHA3,
            Opcodes.ADDRESS,
            Opcodes.BALANCE,
            Opcodes.ORIGIN,
            Opcodes.CALLER,
            Opcodes.CALLVALUE,
            Opcodes.CALLDATALOAD,
            Opcodes.CALLDATASIZE,
            Opcodes.CALLDATACOPY,
            Opcodes.CODESIZE,
            Opcodes.CODECOPY,
            Opcodes.GASPRICE,
            Opcodes.EXTCODESIZE,
            Opcodes.EXTCODECOPY,
            Opcodes.BLOCKHASH,
            Opcodes.COINBASE,
            Opcodes.TIMESTAMP,
            Opcodes.NUMBER,
            Opcodes.PREVRANDAO,
            Opcodes.GASLIMIT,
            Opcodes.POP,
            Opcodes.MLOAD,
            Opcodes.MSTORE,
            Opcodes.MSTORE8,
            Opcodes.SLOAD,
            Opcodes.SSTORE,
            Opcodes.PC,
            Opcodes.MSIZE,
            Opcodes.GAS,
            Opcodes.JUMP,
            Opcodes.JUMPI,
            Opcodes.JUMPDEST,
            Opcodes.PUSH1,
            Opcodes.PUSH2,
            Opcodes.PUSH3,
            Opcodes.PUSH4,
            Opcodes.PUSH5,
            Opcodes.PUSH6,
            Opcodes.PUSH7,
            Opcodes.PUSH8,
            Opcodes.PUSH9,
            Opcodes.PUSH10,
            Opcodes.PUSH11,
            Opcodes.PUSH12,
            Opcodes.PUSH13,
            Opcodes.PUSH14,
            Opcodes.PUSH15,
            Opcodes.PUSH16,
            Opcodes.PUSH17,
            Opcodes.PUSH18,
            Opcodes.PUSH19,
            Opcodes.PUSH20,
            Opcodes.PUSH21,
            Opcodes.PUSH22,
            Opcodes.PUSH23,
            Opcodes.PUSH24,
            Opcodes.PUSH25,
            Opcodes.PUSH26,
            Opcodes.PUSH27,
            Opcodes.PUSH28,
            Opcodes.PUSH29,
            Opcodes.PUSH30,
            Opcodes.PUSH31,
            Opcodes.PUSH32,
            Opcodes.DUP1,
            Opcodes.DUP2,
            Opcodes.DUP3,
            Opcodes.DUP4,
            Opcodes.DUP5,
            Opcodes.DUP6,
            Opcodes.DUP7,
            Opcodes.DUP8,
            Opcodes.DUP9,
            Opcodes.DUP10,
            Opcodes.DUP11,
            Opcodes.DUP12,
            Opcodes.DUP13,
            Opcodes.DUP14,
            Opcodes.DUP15,
            Opcodes.DUP16,
            Opcodes.SWAP1,
            Opcodes.SWAP2,
            Opcodes.SWAP3,
            Opcodes.SWAP4,
            Opcodes.SWAP5,
            Opcodes.SWAP6,
            Opcodes.SWAP7,
            Opcodes.SWAP8,
            Opcodes.SWAP9,
            Opcodes.SWAP10,
            Opcodes.SWAP11,
            Opcodes.SWAP12,
            Opcodes.SWAP13,
            Opcodes.SWAP14,
            Opcodes.SWAP15,
            Opcodes.SWAP16,
            Opcodes.LOG0,
            Opcodes.LOG1,
            Opcodes.LOG2,
            Opcodes.LOG3,
            Opcodes.LOG4,
            Opcodes.CREATE,
            Opcodes.CALL,
            Opcodes.CALLCODE,
            Opcodes.RETURN,
            Opcodes.SELFDESTRUCT,
        ]

    @classmethod
    def create_opcodes(cls) -> List[Opcodes]:
        """At Genesis, only `CREATE` opcode is supported."""
        return [Opcodes.CREATE]

    @classmethod
    def max_refund_quotient(cls) -> int:
        """Return the max refund quotient at Genesis."""
        return 2

    @classmethod
    def max_request_type(cls) -> int:
        """At genesis, no request type is supported, signaled by -1."""
        return -1

    @classmethod
    def refund_types(cls) -> List[RefundTypes]:
        """
        At genesis, storage clearing refund is introduced.
        """
        return [RefundTypes.STORAGE_CLEAR]

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """
        Return whether the fork expects pre-allocation of accounts.

        Frontier does not require pre-allocated accounts
        """
        return {}

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Return whether the fork expects pre-allocation of accounts.

        Frontier does not require pre-allocated accounts
        """
        return {}

    @classmethod
    def build_default_block_header(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> FixtureHeader:
        """
        Build a default block header for this fork with the given attributes.

        This method automatically detects which header fields are required by
        the fork and assigns appropriate default values. It introspects the
        FixtureHeader model to find fields with HeaderForkRequirement
        annotations and automatically includes them if the fork requires them.

        Args:
            block_number: The block number
            timestamp: The block timestamp

        Returns:
            FixtureHeader instance with default values applied based on fork
            requirements.

        Raises:
            TypeError: If the overrides don't have the correct type.

        """
        from execution_testing.fixtures.blockchain import FixtureHeader

        defaults = {
            "number": ZeroPaddedHexNumber(block_number),
            "timestamp": ZeroPaddedHexNumber(timestamp),
            "fork": cls,
        }

        # Iterate through FixtureHeader fields to populate defaults
        for field_name, field_info in FixtureHeader.model_fields.items():
            if field_name in defaults:
                continue

            # Get default value, checking fork requirements and model defaults
            default_value = FixtureHeader.get_default_from_annotation(
                fork=cls,
                field_name=field_name,
                field_hint=field_info.annotation,
            )
            if default_value is not None:
                defaults[field_name] = default_value

        return FixtureHeader(**defaults)


class Homestead(
    eips.EIP7,
    eips.EIP2,
    Frontier,
):
    """Homestead fork."""

    pass


class DAOFork(
    Homestead,
    ignore=True,
    ruleset_name="",
):
    """DAO fork."""

    pass


class TangerineWhistle(
    DAOFork,
    ignore=True,
    ruleset_name="TANGERINE",
):
    """TangerineWhistle fork (EIP-150)."""

    pass


class SpuriousDragon(
    eips.EIP170,
    eips.EIP161,
    eips.EIP155,
    TangerineWhistle,
    ignore=True,
    ruleset_name="SPURIOUS",
):
    """SpuriousDragon fork."""

    pass


class Byzantium(
    eips.EIP649,
    eips.EIP214,
    eips.EIP211,
    eips.EIP140,
    eips.EIP198,
    eips.EIP196,
    eips.EIP197,
    SpuriousDragon,
):
    """Byzantium fork."""

    pass


class Constantinople(
    eips.EIP1234,
    eips.EIP1052,
    eips.EIP1014,
    eips.EIP145,
    Byzantium,
):
    """Constantinople fork."""

    pass


class ConstantinopleFix(
    Constantinople,
    solc_name="constantinople",
    ruleset_name="PETERSBURG",
):
    """Constantinople Fix fork."""

    pass


class Istanbul(
    eips.EIP2028,
    eips.EIP1884,
    eips.EIP1344,
    eips.EIP1108,
    eips.EIP152,
    ConstantinopleFix,
):
    """Istanbul fork."""

    pass


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(
    Istanbul,
    solc_name="istanbul",
    ignore=True,
):
    """Muir Glacier fork."""

    pass


class Berlin(
    eips.EIP2930,
    Istanbul,
):
    """Berlin fork."""

    pass


class London(
    eips.EIP3529,
    eips.EIP3198,
    eips.EIP1559,
    Berlin,
):
    """London fork."""

    pass


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(
    London,
    solc_name="london",
    ignore=True,
):
    """Arrow Glacier fork."""

    pass


class GrayGlacier(
    ArrowGlacier,
    solc_name="london",
    ignore=True,
):
    """Gray Glacier fork."""

    pass


class Paris(
    eips.EIP3675,
    London,
    transition_tool_name="Merge",
    ruleset_name="MERGE",
):
    """Paris (Merge) fork."""

    pass


class Shanghai(
    eips.EIP3855,
    eips.EIP3860,
    eips.EIP4895,
    Paris,
    fork_by_timestamp=True,
):
    """Shanghai fork."""

    pass


class Cancun(
    eips.EIP5656,
    eips.EIP1153,
    eips.EIP4788,
    eips.EIP4844,
    eips.EIP7516,
    eips.EIP6780,
    Shanghai,
):
    """Cancun fork."""

    pass


class Prague(
    eips.EIP7691,
    eips.EIP7685,
    eips.EIP2935,
    eips.EIP7251,
    eips.EIP7002,
    eips.EIP6110,
    eips.EIP7623,
    eips.EIP7702,
    eips.EIP2537,
    Cancun,
):
    """Prague fork."""

    pass


class Osaka(
    eips.EIP7939,
    eips.EIP7934,
    eips.EIP7825,
    eips.EIP7918,
    eips.EIP7594,
    eips.EIP7951,
    Prague,
    solc_name="cancun",
):
    """Osaka fork."""

    pass


class BPO1(
    Osaka,
    bpo_fork=True,
    update_blob_constants={
        "BLOB_BASE_FEE_UPDATE_FRACTION": 8346193,
        "TARGET_BLOBS_PER_BLOCK": 10,
        "MAX_BLOBS_PER_BLOCK": 15,
    },
):
    """Mainnet BPO1 fork - Blob Parameter Only fork 1."""

    pass


class BPO2(
    BPO1,
    bpo_fork=True,
    update_blob_constants={
        "BLOB_BASE_FEE_UPDATE_FRACTION": 11684671,
        "TARGET_BLOBS_PER_BLOCK": 14,
        "MAX_BLOBS_PER_BLOCK": 21,
    },
):
    """Mainnet BPO2 fork - Blob Parameter Only fork 2."""

    pass


class BPO3(
    BPO2,
    bpo_fork=True,
    deployed=False,
    update_blob_constants={
        "BLOB_BASE_FEE_UPDATE_FRACTION": 20609697,
        "TARGET_BLOBS_PER_BLOCK": 21,
        "MAX_BLOBS_PER_BLOCK": 32,
    },
):
    """
    Pseudo BPO3 fork - Blob Parameter Only fork 3.
    For testing purposes only.
    """

    pass


class BPO4(
    BPO3,
    bpo_fork=True,
    update_blob_constants={
        "BLOB_BASE_FEE_UPDATE_FRACTION": 13739630,
        "TARGET_BLOBS_PER_BLOCK": 14,
        "MAX_BLOBS_PER_BLOCK": 21,
    },
):
    """
    Pseudo BPO4 fork - Blob Parameter Only fork 4.
    For testing purposes only. Testing a decrease in values from BPO3.
    """

    pass


class BPO5(
    BPO4,
    bpo_fork=True,
):
    """
    Pseudo BPO5 fork - Blob Parameter Only fork 5.
    For testing purposes only. Required to parse Fusaka devnet genesis files.
    """

    pass


class Amsterdam(
    AmsterdamEIPs,
    BPO2,
    deployed=False,
):
    """Amsterdam fork."""

    # TODO: We may need to adjust which BPO Amsterdam inherits from as the
    #  related Amsterdam specs change over time, and before Amsterdam is
    #  live on mainnet.

    pass
