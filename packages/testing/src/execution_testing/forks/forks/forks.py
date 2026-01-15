"""All Ethereum fork class definitions."""

from dataclasses import replace
from hashlib import sha256
from os.path import realpath
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sized,
    Tuple,
)

from execution_testing.base_types import (
    AccessList,
    Address,
    BlobSchedule,
    Bytes,
    ForkBlobSchedule,
)
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import (
    EVMCodeType,
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
    TransactionDataFloorCostCalculator,
    TransactionIntrinsicCostCalculator,
)
from ..gas_costs import GasCosts
from .helpers import ceiling_division, fake_exponential

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


# All forks must be listed here !!! in the order they were introduced !!!
class Frontier(BaseFork, solc_name="homestead"):
    """Frontier fork."""

    @classmethod
    def transition_tool_name(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> str:
        """
        Return fork name as it's meant to be passed to the transition tool for
        execution.
        """
        del block_number, timestamp
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
    def header_base_fee_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain base fee."""
        del block_number, timestamp
        return False

    @classmethod
    def header_prev_randao_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain Prev Randao value."""
        del block_number, timestamp
        return False

    @classmethod
    def header_zero_difficulty_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not have difficulty zero."""
        del block_number, timestamp
        return False

    @classmethod
    def header_withdrawals_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain withdrawals."""
        del block_number, timestamp
        return False

    @classmethod
    def header_excess_blob_gas_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain excess blob gas."""
        del block_number, timestamp
        return False

    @classmethod
    def header_blob_gas_used_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain blob gas used."""
        del block_number, timestamp
        return False

    @classmethod
    def gas_costs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> GasCosts:
        """
        Return dataclass with the defined gas costs constants for genesis.
        """
        del block_number, timestamp
        return GasCosts(
            G_JUMPDEST=1,
            G_BASE=2,
            G_VERY_LOW=3,
            G_LOW=5,
            G_MID=8,
            G_HIGH=10,
            G_WARM_ACCOUNT_ACCESS=100,
            G_COLD_ACCOUNT_ACCESS=2_600,
            G_ACCESS_LIST_ADDRESS=2_400,
            G_ACCESS_LIST_STORAGE=1_900,
            G_WARM_SLOAD=100,
            G_COLD_SLOAD=2_100,
            G_STORAGE_SET=20_000,
            G_STORAGE_UPDATE=5_000,
            G_STORAGE_RESET=2_900,
            R_STORAGE_CLEAR=4_800,
            G_SELF_DESTRUCT=5_000,
            G_CREATE=32_000,
            G_CODE_DEPOSIT_BYTE=200,
            G_INITCODE_WORD=2,
            G_CALL_VALUE=9_000,
            G_CALL_STIPEND=2_300,
            G_NEW_ACCOUNT=25_000,
            G_EXP=10,
            G_EXP_BYTE=50,
            G_MEMORY=3,
            G_TX_DATA_ZERO=4,
            G_TX_DATA_NON_ZERO=68,
            G_TX_DATA_STANDARD_TOKEN_COST=0,
            G_TX_DATA_FLOOR_TOKEN_COST=0,
            G_TRANSACTION=21_000,
            G_TRANSACTION_CREATE=32_000,
            G_LOG=375,
            G_LOG_DATA=8,
            G_LOG_TOPIC=375,
            G_KECCAK_256=30,
            G_KECCAK_256_WORD=6,
            G_COPY=3,
            G_BLOCKHASH=20,
            G_AUTHORIZATION=0,
            R_AUTHORIZATION_EXISTING_AUTHORITY=0,
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
                access_cost = gas_costs.G_WARM_ACCOUNT_ACCESS
            else:
                access_cost = gas_costs.G_COLD_ACCOUNT_ACCESS

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
            gas_costs: The gas costs dataclass for accessing G_COPY

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
            copy_cost = gas_costs.G_COPY * word_count

            return base_cost + copy_cost

        return wrapper

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas costs.

        Each entry is either:
        - Constants (int): Direct gas cost values from gas_costs()
        - Callables: Functions that take the opcode instance with metadata and
                     return gas cost
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        memory_expansion_calculator = cls.memory_expansion_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )

        # Define the opcode gas cost mapping
        # Each entry is either:
        # - an int (constant cost)
        # - a callable(opcode) -> int
        return {
            # Stop and arithmetic operations
            Opcodes.STOP: 0,
            Opcodes.ADD: gas_costs.G_VERY_LOW,
            Opcodes.MUL: gas_costs.G_LOW,
            Opcodes.SUB: gas_costs.G_VERY_LOW,
            Opcodes.DIV: gas_costs.G_LOW,
            Opcodes.SDIV: gas_costs.G_LOW,
            Opcodes.MOD: gas_costs.G_LOW,
            Opcodes.SMOD: gas_costs.G_LOW,
            Opcodes.ADDMOD: gas_costs.G_MID,
            Opcodes.MULMOD: gas_costs.G_MID,
            Opcodes.EXP: lambda op: gas_costs.G_EXP
            + gas_costs.G_EXP_BYTE
            * ((op.metadata["exponent"].bit_length() + 7) // 8),
            Opcodes.SIGNEXTEND: gas_costs.G_LOW,
            # Comparison & bitwise logic operations
            Opcodes.LT: gas_costs.G_VERY_LOW,
            Opcodes.GT: gas_costs.G_VERY_LOW,
            Opcodes.SLT: gas_costs.G_VERY_LOW,
            Opcodes.SGT: gas_costs.G_VERY_LOW,
            Opcodes.EQ: gas_costs.G_VERY_LOW,
            Opcodes.ISZERO: gas_costs.G_VERY_LOW,
            Opcodes.AND: gas_costs.G_VERY_LOW,
            Opcodes.OR: gas_costs.G_VERY_LOW,
            Opcodes.XOR: gas_costs.G_VERY_LOW,
            Opcodes.NOT: gas_costs.G_VERY_LOW,
            Opcodes.BYTE: gas_costs.G_VERY_LOW,
            # SHA3
            Opcodes.SHA3: cls._with_memory_expansion(
                lambda op: gas_costs.G_KECCAK_256
                + gas_costs.G_KECCAK_256_WORD
                * ((op.metadata["data_size"] + 31) // 32),
                memory_expansion_calculator,
            ),
            # Environmental information
            Opcodes.ADDRESS: gas_costs.G_BASE,
            Opcodes.BALANCE: cls._with_account_access(0, gas_costs),
            Opcodes.ORIGIN: gas_costs.G_BASE,
            Opcodes.CALLER: gas_costs.G_BASE,
            Opcodes.CALLVALUE: gas_costs.G_BASE,
            Opcodes.CALLDATALOAD: gas_costs.G_VERY_LOW,
            Opcodes.CALLDATASIZE: gas_costs.G_BASE,
            Opcodes.CALLDATACOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.G_VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.CODESIZE: gas_costs.G_BASE,
            Opcodes.CODECOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.G_VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.GASPRICE: gas_costs.G_BASE,
            Opcodes.EXTCODESIZE: cls._with_account_access(0, gas_costs),
            Opcodes.EXTCODECOPY: cls._with_memory_expansion(
                cls._with_data_copy(
                    cls._with_account_access(0, gas_costs),
                    gas_costs,
                ),
                memory_expansion_calculator,
            ),
            # Block information
            Opcodes.BLOCKHASH: gas_costs.G_BLOCKHASH,
            Opcodes.COINBASE: gas_costs.G_BASE,
            Opcodes.TIMESTAMP: gas_costs.G_BASE,
            Opcodes.NUMBER: gas_costs.G_BASE,
            Opcodes.PREVRANDAO: gas_costs.G_BASE,
            Opcodes.GASLIMIT: gas_costs.G_BASE,
            # Stack, memory, storage and flow operations
            Opcodes.POP: gas_costs.G_BASE,
            Opcodes.MLOAD: cls._with_memory_expansion(
                gas_costs.G_VERY_LOW, memory_expansion_calculator
            ),
            Opcodes.MSTORE: cls._with_memory_expansion(
                gas_costs.G_VERY_LOW, memory_expansion_calculator
            ),
            Opcodes.MSTORE8: cls._with_memory_expansion(
                gas_costs.G_VERY_LOW, memory_expansion_calculator
            ),
            Opcodes.SLOAD: lambda op: gas_costs.G_WARM_SLOAD
            if op.metadata["key_warm"]
            else gas_costs.G_COLD_SLOAD,
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_gas(
                op, gas_costs
            ),
            Opcodes.JUMP: gas_costs.G_MID,
            Opcodes.JUMPI: gas_costs.G_HIGH,
            Opcodes.PC: gas_costs.G_BASE,
            Opcodes.MSIZE: gas_costs.G_BASE,
            Opcodes.GAS: gas_costs.G_BASE,
            Opcodes.JUMPDEST: gas_costs.G_JUMPDEST,
            # Push operations (PUSH1 through PUSH32)
            **{
                getattr(Opcodes, f"PUSH{i}"): gas_costs.G_VERY_LOW
                for i in range(1, 33)
            },
            # Dup operations (DUP1 through DUP16)
            **{
                getattr(Opcodes, f"DUP{i}"): gas_costs.G_VERY_LOW
                for i in range(1, 17)
            },
            # Swap operations (SWAP1 through SWAP16)
            **{
                getattr(Opcodes, f"SWAP{i}"): gas_costs.G_VERY_LOW
                for i in range(1, 17)
            },
            # Logging operations
            Opcodes.LOG0: cls._with_memory_expansion(
                lambda op: gas_costs.G_LOG
                + gas_costs.G_LOG_DATA * op.metadata["data_size"],
                memory_expansion_calculator,
            ),
            Opcodes.LOG1: cls._with_memory_expansion(
                lambda op: gas_costs.G_LOG
                + gas_costs.G_LOG_DATA * op.metadata["data_size"]
                + gas_costs.G_LOG_TOPIC,
                memory_expansion_calculator,
            ),
            Opcodes.LOG2: cls._with_memory_expansion(
                lambda op: gas_costs.G_LOG
                + gas_costs.G_LOG_DATA * op.metadata["data_size"]
                + gas_costs.G_LOG_TOPIC * 2,
                memory_expansion_calculator,
            ),
            Opcodes.LOG3: cls._with_memory_expansion(
                lambda op: gas_costs.G_LOG
                + gas_costs.G_LOG_DATA * op.metadata["data_size"]
                + gas_costs.G_LOG_TOPIC * 3,
                memory_expansion_calculator,
            ),
            Opcodes.LOG4: cls._with_memory_expansion(
                lambda op: gas_costs.G_LOG
                + gas_costs.G_LOG_DATA * op.metadata["data_size"]
                + gas_costs.G_LOG_TOPIC * 4,
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
    def opcode_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas cost of a single opcode.
        """
        opcode_gas_map = cls.opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )

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
    def opcode_refund_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas refunds.

        Each entry is either:
        - Constants (int): Direct gas refund values
        - Callables: Functions that take the opcode instance with metadata and
                     return gas refund
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        # Only SSTORE provides refunds
        return {
            Opcodes.SSTORE: lambda op: cls._calculate_sstore_refund(
                op, gas_costs
            ),
        }

    @classmethod
    def opcode_refund_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> OpcodeGasCalculator:
        """
        Return callable that calculates the gas refund of a single opcode.
        """
        opcode_refund_map = cls.opcode_refund_map(
            block_number=block_number, timestamp=timestamp
        )

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
                refund += gas_costs.R_STORAGE_CLEAR

            if original_value != 0 and current_value == 0:
                # Gas refund issued earlier to be reversed
                refund -= gas_costs.R_STORAGE_CLEAR

            if original_value == new_value:
                # Storage slot being restored to its original value
                if original_value == 0:
                    # Slot was originally empty and was SET earlier
                    refund += gas_costs.G_STORAGE_SET - gas_costs.G_WARM_SLOAD
                else:
                    # Slot was originally non-empty and was UPDATED earlier
                    refund += (
                        gas_costs.G_STORAGE_UPDATE
                        - gas_costs.G_COLD_SLOAD
                        - gas_costs.G_WARM_SLOAD
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

        gas_cost = 0 if metadata["key_warm"] else gas_costs.G_COLD_SLOAD

        if original_value == current_value and current_value != new_value:
            if original_value == 0:
                gas_cost += gas_costs.G_STORAGE_SET
            else:
                gas_cost += gas_costs.G_STORAGE_UPDATE - gas_costs.G_COLD_SLOAD
        else:
            gas_cost += gas_costs.G_WARM_SLOAD

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
            base_cost = gas_costs.G_WARM_ACCOUNT_ACCESS
        else:
            base_cost = gas_costs.G_COLD_ACCOUNT_ACCESS

        return base_cost

    @classmethod
    def _calculate_create_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """CREATE gas is constant at Frontier."""
        del opcode
        return gas_costs.G_CREATE

    @classmethod
    def _calculate_return_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate RETURN gas cost based on metadata."""
        metadata = opcode.metadata

        # Code deposit cost when returning from initcode
        code_deposit_size = metadata["code_deposit_size"]
        return gas_costs.G_CODE_DEPOSIT_BYTE * code_deposit_size

    @classmethod
    def _calculate_selfdestruct_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate SELFDESTRUCT gas cost based on metadata."""
        metadata = opcode.metadata

        base_cost = gas_costs.G_SELF_DESTRUCT

        # Check if the beneficiary is cold
        if not metadata["address_warm"]:
            base_cost += gas_costs.G_COLD_ACCOUNT_ACCESS

        # Check if creating a new account
        if metadata["account_new"]:
            base_cost += gas_costs.G_NEW_ACCOUNT

        return base_cost

    @classmethod
    def memory_expansion_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> MemoryExpansionGasCalculator:
        """
        Return callable that calculates the gas cost of memory expansion for
        the fork.
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(*, new_bytes: int, previous_bytes: int = 0) -> int:
            if new_bytes <= previous_bytes:
                return 0
            new_words = ceiling_division(new_bytes, 32)
            previous_words = ceiling_division(previous_bytes, 32)

            def c(w: int) -> int:
                return (gas_costs.G_MEMORY * w) + ((w * w) // 512)

            return c(new_words) - c(previous_words)

        return fn

    @classmethod
    def calldata_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> CalldataGasCalculator:
        """
        Return callable that calculates the transaction gas cost for its
        calldata depending on its contents.
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(*, data: BytesConvertible, floor: bool = False) -> int:
            del floor

            cost = 0
            for b in Bytes(data):
                if b == 0:
                    cost += gas_costs.G_TX_DATA_ZERO
                else:
                    cost += gas_costs.G_TX_DATA_NON_ZERO
            return cost

        return fn

    @classmethod
    def base_fee_per_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BaseFeePerGasCalculator:
        """
        Return a callable that calculates the base fee per gas at a given fork.
        """
        raise NotImplementedError(
            f"Base fee per gas calculator is not supported in {cls.name()}"
        )

    @classmethod
    def base_fee_change_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BaseFeeChangeCalculator:
        """
        Return a callable that calculates the gas that needs to be used to
        change the base fee.
        """
        raise NotImplementedError(
            f"Base fee change calculator is not supported in {cls.name()}"
        )

    @classmethod
    def base_fee_max_change_denominator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base fee max change denominator at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Base fee max change denominator is not supported in {cls.name()}"
        )

    @classmethod
    def base_fee_elasticity_multiplier(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base fee elasticity multiplier at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Base fee elasticity multiplier is not supported in {cls.name()}"
        )

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionDataFloorCostCalculator:
        """At frontier, the transaction data floor cost is a constant zero."""
        del block_number, timestamp

        def fn(*, data: BytesConvertible) -> int:
            del data
            return 0

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionIntrinsicCostCalculator:
        """
        Return callable that calculates the intrinsic gas cost of a transaction
        for the fork.
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        calldata_gas_calculator = cls.calldata_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )

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

            intrinsic_cost: int = gas_costs.G_TRANSACTION

            if contract_creation:
                intrinsic_cost += gas_costs.G_INITCODE_WORD * ceiling_division(
                    len(Bytes(calldata)), 32
                )

            return intrinsic_cost + calldata_gas_calculator(data=calldata)

        return fn

    @classmethod
    def blob_gas_price_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BlobGasPriceCalculator:
        """
        Return a callable that calculates the blob gas price at a given fork.
        """
        raise NotImplementedError(
            f"Blob gas price calculator is not supported in {cls.name()}"
        )

    @classmethod
    def excess_blob_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block at a
        given fork.
        """
        raise NotImplementedError(
            f"Excess blob gas calculator is not supported in {cls.name()}"
        )

    @classmethod
    def min_base_fee_per_blob_gas(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the amount of blob gas used per blob at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Base fee per blob gas is not supported in {cls.name()}"
        )

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Blob base fee update fraction is not supported in {cls.name()}"
        )

    @classmethod
    def blob_gas_per_blob(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the amount of blob gas used per blob at a given fork."""
        del block_number, timestamp
        return 0

    @classmethod
    def supports_blobs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Blobs are not supported at Frontier."""
        del block_number, timestamp
        return False

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the target number of blobs per block at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Target blobs per block is not supported in {cls.name()}"
        )

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the max number of blobs per block at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Max blobs per block is not supported in {cls.name()}"
        )

    @classmethod
    def blob_reserve_price_active(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """
        Return whether the fork uses a reserve price mechanism for blobs or
        not.
        """
        del block_number, timestamp
        raise NotImplementedError(
            f"Blob reserve price is not supported in {cls.name()}"
        )

    @classmethod
    def blob_base_cost(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base cost of a blob at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Blob base cost is not supported in {cls.name()}"
        )

    @classmethod
    def full_blob_tx_wrapper_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """Return the version of the full blob transaction wrapper."""
        raise NotImplementedError(
            "Full blob transaction wrapper version is not supported in "
            f"{cls.name()}"
        )

    @classmethod
    def max_blobs_per_tx(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the max number of blobs per tx at a given fork."""
        del block_number, timestamp
        raise NotImplementedError(
            f"Max blobs per tx is not supported in {cls.name()}"
        )

    @classmethod
    def blob_schedule(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BlobSchedule | None:
        """At genesis, no blob schedule is used."""
        del block_number, timestamp
        return None

    @classmethod
    def header_requests_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain beacon chain requests."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """At genesis, payloads cannot be sent through the engine API."""
        del block_number, timestamp
        return None

    @classmethod
    def header_beacon_root_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, header must not contain parent beacon block root."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_new_payload_blob_hashes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, payloads do not have blob hashes."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_new_payload_beacon_root(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, payloads do not have a parent beacon block root."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_new_payload_requests(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At genesis, payloads do not have requests."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_new_payload_target_blobs_per_block(
        cls,
        *,
        block_number: int = 0,
        timestamp: int = 0,
    ) -> bool:
        """At genesis, payloads do not have target blobs per block."""
        del block_number, timestamp
        return False

    @classmethod
    def engine_payload_attribute_target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """
        At genesis, payload attributes do not include the target blobs per
        block.
        """
        del block_number, timestamp
        return False

    @classmethod
    def engine_payload_attribute_max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """
        At genesis, payload attributes do not include the max blobs per block.
        """
        del block_number, timestamp
        return False

    @classmethod
    def engine_forkchoice_updated_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        At genesis, forkchoice updates cannot be sent through the engine API.
        """
        return cls.engine_new_payload_version(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def engine_get_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """At genesis, payloads cannot be retrieved through the engine API."""
        return cls.engine_new_payload_version(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def engine_get_blobs_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """At genesis, blobs cannot be retrieved through the engine API."""
        del block_number, timestamp
        return None

    @classmethod
    def get_reward(cls, *, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Genesis the expected reward amount in wei is
        5_000_000_000_000_000_000.
        """
        del block_number, timestamp
        return 5_000_000_000_000_000_000

    @classmethod
    def tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Genesis, only legacy transactions are allowed."""
        del block_number, timestamp
        return [0]

    @classmethod
    def contract_creating_tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Genesis, only legacy transactions are allowed."""
        del block_number, timestamp
        return [0]

    @classmethod
    def transaction_gas_limit_cap(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """At Genesis, no transaction gas limit cap is imposed."""
        del block_number, timestamp
        return None

    @classmethod
    def block_rlp_size_limit(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """At Genesis, no RLP block size limit is imposed."""
        del block_number, timestamp
        return None

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """At Genesis, no precompiles are present."""
        del block_number, timestamp
        return []

    @classmethod
    def system_contracts(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """At Genesis, no system contracts are present."""
        del block_number, timestamp
        return []

    @classmethod
    def deterministic_factory_predeploy_address(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Address | None:
        """At Genesis, no deterministic factory predeploy is present."""
        del block_number, timestamp
        return None

    @classmethod
    def evm_code_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[EVMCodeType]:
        """At Genesis, only legacy EVM code is supported."""
        del block_number, timestamp
        return [EVMCodeType.LEGACY]

    @classmethod
    def max_code_size(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        At genesis, there is no upper bound for code size (bounded by block gas
        limit).

        However, the default is set to the limit of EIP-170 (Spurious Dragon)
        """
        del block_number, timestamp
        return 0x6000

    @classmethod
    def max_stack_height(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """At genesis, the maximum stack height is 1024."""
        del block_number, timestamp
        return 1024

    @classmethod
    def max_initcode_size(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        At genesis, there is no upper bound for initcode size.

        However, the default is set to the limit of EIP-3860 (Shanghai).
        """
        del block_number, timestamp
        return 0xC000

    @classmethod
    def call_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """Return list of call opcodes supported by the fork."""
        del block_number, timestamp
        return [
            (Opcodes.CALL, EVMCodeType.LEGACY),
            (Opcodes.CALLCODE, EVMCodeType.LEGACY),
        ]

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
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
    def create_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """At Genesis, only `CREATE` opcode is supported."""
        del block_number, timestamp
        return [
            (Opcodes.CREATE, EVMCodeType.LEGACY),
        ]

    @classmethod
    def max_refund_quotient(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the max refund quotient at Genesis."""
        del block_number, timestamp
        return 2

    @classmethod
    def max_request_type(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """At genesis, no request type is supported, signaled by -1."""
        del block_number, timestamp
        return -1

    @classmethod
    def pre_allocation(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Mapping:
        """
        Return whether the fork expects pre-allocation of accounts.

        Frontier does not require pre-allocated accounts
        """
        del block_number, timestamp
        return {}

    @classmethod
    def pre_allocation_blockchain(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Mapping:
        """
        Return whether the fork expects pre-allocation of accounts.

        Frontier does not require pre-allocated accounts
        """
        del block_number, timestamp
        return {}


class Homestead(Frontier):
    """Homestead fork."""

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """
        At Homestead, EC-recover, SHA256, RIPEMD160, and Identity precompiles
        are introduced.
        """
        return [
            Address(1, label="ECREC"),
            Address(2, label="SHA256"),
            Address(3, label="RIPEMD160"),
            Address(4, label="ID"),
        ] + super(Homestead, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def call_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """At Homestead, DELEGATECALL opcode was introduced."""
        return [(Opcodes.DELEGATECALL, EVMCodeType.LEGACY)] + super(
            Homestead, cls
        ).call_opcodes(block_number=block_number, timestamp=timestamp)

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add DELEGATECALL opcode gas cost for Homestead."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        memory_expansion_calculator = cls.memory_expansion_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Homestead, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.DELEGATECALL: cls._with_memory_expansion(
                lambda op: cls._calculate_call_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return the list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [Opcodes.DELEGATECALL] + super(Homestead, cls).valid_opcodes()

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionIntrinsicCostCalculator:
        """
        At Homestead, the transaction intrinsic cost needs to take contract
        creation into account.
        """
        super_fn = super(Homestead, cls).transaction_intrinsic_cost_calculator(
            block_number=block_number, timestamp=timestamp
        )
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            del return_cost_deducted_prior_execution

            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                authorization_list_or_count=authorization_list_or_count,
            )
            if contract_creation:
                intrinsic_cost += gas_costs.G_TRANSACTION_CREATE
            return intrinsic_cost

        return fn


class DAOFork(Homestead, ignore=True):
    """DAO fork."""

    pass


class Tangerine(DAOFork, ignore=True):
    """Tangerine fork (EIP-150)."""

    pass


class SpuriousDragon(Tangerine, ignore=True):
    """SpuriousDragon fork (EIP-155, EIP-158)."""

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        At Spurious Dragon, the call gas cost needs to take the value transfer
        and account new into account.
        """
        base_cost = super(SpuriousDragon, cls)._calculate_call_gas(
            opcode, gas_costs
        )

        # Additional costs for value transfer, does not apply to STATICCALL
        metadata = opcode.metadata
        if "value_transfer" in metadata:
            if metadata["value_transfer"]:
                base_cost += gas_costs.G_CALL_VALUE
                if metadata["account_new"]:
                    base_cost += gas_costs.G_NEW_ACCOUNT
            elif metadata["account_new"]:
                raise ValueError("Account new requires value transfer")

        return base_cost


class Byzantium(SpuriousDragon):
    """Byzantium fork."""

    @classmethod
    def get_reward(cls, *, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Byzantium, the block reward is reduced to 3_000_000_000_000_000_000
        wei.
        """
        del block_number, timestamp
        return 3_000_000_000_000_000_000

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """
        At Byzantium, precompiles for bigint modular exponentiation, addition
        and scalar multiplication on elliptic curve alt_bn128, and optimal ate
        pairing check on elliptic curve alt_bn128 are introduced.
        """
        return [
            Address(5, label="MODEXP"),
            Address(6, label="BN254_ADD"),
            Address(7, label="BN254_MUL"),
            Address(8, label="BN254_PAIRING"),
        ] + super(Byzantium, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def max_code_size(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        # NOTE: Move this to Spurious Dragon once this fork is introduced. See
        # EIP-170.
        """
        At Spurious Dragon, an upper bound was introduced for max contract code
        size.
        """
        del block_number, timestamp
        return 0x6000

    @classmethod
    def call_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """At Byzantium, STATICCALL opcode was introduced."""
        return [(Opcodes.STATICCALL, EVMCodeType.LEGACY)] + super(
            Byzantium, cls
        ).call_opcodes(block_number=block_number, timestamp=timestamp)

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add Byzantium opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        memory_expansion_calculator = cls.memory_expansion_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Byzantium, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.RETURNDATASIZE: gas_costs.G_BASE,
            Opcodes.RETURNDATACOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.G_VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.STATICCALL: cls._with_memory_expansion(
                lambda op: cls._calculate_call_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
            Opcodes.REVERT: cls._with_memory_expansion(
                0, memory_expansion_calculator
            ),
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [
            Opcodes.REVERT,
            Opcodes.RETURNDATASIZE,
            Opcodes.RETURNDATACOPY,
            Opcodes.STATICCALL,
        ] + super(Byzantium, cls).valid_opcodes()

    @classmethod
    def gas_costs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> GasCosts:
        """
        On Byzantium, precompiled contract gas costs are introduced.
        """
        return replace(
            super(Byzantium, cls).gas_costs(
                block_number=block_number, timestamp=timestamp
            ),
            G_PRECOMPILE_ECADD=500,
            G_PRECOMPILE_ECMUL=40_000,
            G_PRECOMPILE_ECPAIRING_BASE=100_000,
            G_PRECOMPILE_ECPAIRING_PER_POINT=80_000,
        )


class Constantinople(Byzantium):
    """Constantinople fork."""

    @classmethod
    def get_reward(cls, *, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Constantinople, the block reward is reduced to
        2_000_000_000_000_000_000 wei.
        """
        del block_number, timestamp
        return 2_000_000_000_000_000_000

    @classmethod
    def _calculate_create2_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """Calculate CREATE2 gas cost based on metadata."""
        metadata = opcode.metadata

        # Keccak256 hashing cost
        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        hash_gas = gas_costs.G_KECCAK_256_WORD * init_code_words

        return gas_costs.G_CREATE + hash_gas

    @classmethod
    def create_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """At Constantinople, `CREATE2` opcode is added."""
        return [(Opcodes.CREATE2, EVMCodeType.LEGACY)] + super(
            Constantinople, cls
        ).create_opcodes(block_number=block_number, timestamp=timestamp)

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add Constantinople opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        memory_expansion_calculator = cls.memory_expansion_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Constantinople, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.SHL: gas_costs.G_VERY_LOW,
            Opcodes.SHR: gas_costs.G_VERY_LOW,
            Opcodes.SAR: gas_costs.G_VERY_LOW,
            Opcodes.EXTCODEHASH: cls._with_account_access(0, gas_costs),
            Opcodes.CREATE2: cls._with_memory_expansion(
                lambda op: cls._calculate_create2_gas(op, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [
            Opcodes.SHL,
            Opcodes.SHR,
            Opcodes.SAR,
            Opcodes.EXTCODEHASH,
            Opcodes.CREATE2,
        ] + super(Constantinople, cls).valid_opcodes()


class ConstantinopleFix(Constantinople, solc_name="constantinople"):
    """Constantinople Fix fork."""

    pass


class Istanbul(ConstantinopleFix):
    """Istanbul fork."""

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """At Istanbul, a precompile for blake2 compression is introduced."""
        return [
            Address(9, label="BLAKE2F"),
        ] + super(Istanbul, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add Istanbul opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Istanbul, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.CHAINID: gas_costs.G_BASE,
            Opcodes.SELFBALANCE: gas_costs.G_LOW,
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [Opcodes.CHAINID, Opcodes.SELFBALANCE] + super(
            Istanbul, cls
        ).valid_opcodes()

    @classmethod
    def gas_costs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> GasCosts:
        """
        On Istanbul, the non-zero transaction data byte cost is reduced to 16
        due to EIP-2028.
        """
        return replace(
            super(Istanbul, cls).gas_costs(
                block_number=block_number, timestamp=timestamp
            ),
            G_TX_DATA_NON_ZERO=16,  # https://eips.ethereum.org/EIPS/eip-2028
            # https://eips.ethereum.org/EIPS/eip-1108
            G_PRECOMPILE_ECADD=150,
            G_PRECOMPILE_ECMUL=6000,
            G_PRECOMPILE_ECPAIRING_BASE=45_000,
            G_PRECOMPILE_ECPAIRING_PER_POINT=34_000,
        )


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(Istanbul, solc_name="istanbul", ignore=True):
    """Muir Glacier fork."""

    pass


class Berlin(Istanbul):
    """Berlin fork."""

    @classmethod
    def tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Berlin, access list transactions are introduced."""
        return [1] + super(Berlin, cls).tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def contract_creating_tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Berlin, access list transactions are introduced."""
        return [1] + super(Berlin, cls).contract_creating_tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionIntrinsicCostCalculator:
        """
        At Berlin, the transaction intrinsic cost needs to take the access list
        into account.
        """
        super_fn = super(Berlin, cls).transaction_intrinsic_cost_calculator(
            block_number=block_number, timestamp=timestamp
        )
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            del return_cost_deducted_prior_execution

            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                authorization_list_or_count=authorization_list_or_count,
            )
            if access_list is not None:
                for access in access_list:
                    intrinsic_cost += gas_costs.G_ACCESS_LIST_ADDRESS
                    for _ in access.storage_keys:
                        intrinsic_cost += gas_costs.G_ACCESS_LIST_STORAGE
            return intrinsic_cost

        return fn


class London(Berlin):
    """London fork."""

    @classmethod
    def header_base_fee_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Header must contain the Base Fee starting from London."""
        del block_number, timestamp
        return True

    @classmethod
    def tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At London, dynamic fee transactions are introduced."""
        return [2] + super(London, cls).tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def contract_creating_tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At London, dynamic fee transactions are introduced."""
        return [2] + super(London, cls).contract_creating_tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add London opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(London, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.BASEFEE: gas_costs.G_BASE,
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [Opcodes.BASEFEE] + super(London, cls).valid_opcodes()

    @classmethod
    def max_refund_quotient(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the max refund quotient at London."""
        del block_number, timestamp
        return 5

    @classmethod
    def base_fee_max_change_denominator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base fee max change denominator at London."""
        del block_number, timestamp
        return 8

    @classmethod
    def base_fee_elasticity_multiplier(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base fee elasticity multiplier at London."""
        del block_number, timestamp
        return 2

    @classmethod
    def base_fee_per_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BaseFeePerGasCalculator:
        """
        Return a callable that calculates the base fee per gas at London.

        EIP-1559 block validation pseudo code:

        if INITIAL_FORK_BLOCK_NUMBER == block.number:
            expected_base_fee_per_gas = INITIAL_BASE_FEE
        elif parent_gas_used == parent_gas_target:
            expected_base_fee_per_gas = parent_base_fee_per_gas
        elif parent_gas_used > parent_gas_target:
            gas_used_delta = parent_gas_used - parent_gas_target
            base_fee_per_gas_delta = max( parent_base_fee_per_gas
                                  * gas_used_delta // parent_gas_target //
                                  BASE_FEE_MAX_CHANGE_DENOMINATOR, 1, )
            expected_base_fee_per_gas = parent_base_fee_per_gas +
                                       base_fee_per_gas_delta
        else:
            gas_used_delta = parent_gas_target - parent_gas_used
            base_fee_per_gas_delta = (
                              parent_base_fee_per_gas * gas_used_delta //
                              parent_gas_target //
                              BASE_FEE_MAX_CHANGE_DENOMINATOR
                              )
            expected_base_fee_per_gas = parent_base_fee_per_gas -
                                        base_fee_per_gas_delta
        """
        base_fee_max_change_denominator = cls.base_fee_max_change_denominator(
            block_number=block_number, timestamp=timestamp
        )
        elasticity_multiplier = cls.base_fee_elasticity_multiplier(
            block_number=block_number, timestamp=timestamp
        )

        def fn(
            *,
            parent_base_fee_per_gas: int,
            parent_gas_used: int,
            parent_gas_limit: int,
        ) -> int:
            parent_gas_target = parent_gas_limit // elasticity_multiplier
            if parent_gas_used == parent_gas_target:
                return parent_base_fee_per_gas
            elif parent_gas_used > parent_gas_target:
                gas_used_delta = parent_gas_used - parent_gas_target
                base_fee_per_gas_delta = max(
                    parent_base_fee_per_gas
                    * gas_used_delta
                    // parent_gas_target
                    // base_fee_max_change_denominator,
                    1,
                )
                return parent_base_fee_per_gas + base_fee_per_gas_delta
            else:
                gas_used_delta = parent_gas_target - parent_gas_used
                base_fee_per_gas_delta = (
                    parent_base_fee_per_gas
                    * gas_used_delta
                    // parent_gas_target
                    // base_fee_max_change_denominator
                )
                return parent_base_fee_per_gas - base_fee_per_gas_delta

        return fn

    @classmethod
    def base_fee_change_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BaseFeeChangeCalculator:
        """
        Return a callable that calculates the gas that needs to be used to
        change the base fee.
        """
        base_fee_max_change_denominator = cls.base_fee_max_change_denominator(
            block_number=block_number, timestamp=timestamp
        )
        elasticity_multiplier = cls.base_fee_elasticity_multiplier(
            block_number=block_number, timestamp=timestamp
        )
        base_fee_per_gas_calculator = cls.base_fee_per_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )

        def fn(
            *,
            parent_base_fee_per_gas: int,
            parent_gas_limit: int,
            required_base_fee_per_gas: int,
        ) -> int:
            parent_gas_target = parent_gas_limit // elasticity_multiplier

            if parent_base_fee_per_gas == required_base_fee_per_gas:
                return parent_gas_target
            elif required_base_fee_per_gas > parent_base_fee_per_gas:
                # Base fee needs to go up, so we need to use more than target
                base_fee_per_gas_delta = (
                    required_base_fee_per_gas - parent_base_fee_per_gas
                )
                parent_gas_used = (
                    (
                        base_fee_per_gas_delta
                        * base_fee_max_change_denominator
                        * parent_gas_target
                    )
                    // parent_base_fee_per_gas
                ) + parent_gas_target
            elif required_base_fee_per_gas < parent_base_fee_per_gas:
                # Base fee needs to go down, so we need to use less than target
                base_fee_per_gas_delta = (
                    parent_base_fee_per_gas - required_base_fee_per_gas
                )

                parent_gas_used = (
                    parent_gas_target
                    - (
                        (
                            base_fee_per_gas_delta
                            * base_fee_max_change_denominator
                            * parent_gas_target
                        )
                        // parent_base_fee_per_gas
                    )
                    - 1
                )

            assert (
                base_fee_per_gas_calculator(
                    parent_base_fee_per_gas=parent_base_fee_per_gas,
                    parent_gas_used=parent_gas_used,
                    parent_gas_limit=parent_gas_limit,
                )
                == required_base_fee_per_gas
            )

            return parent_gas_used

        return fn


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(London, solc_name="london", ignore=True):
    """Arrow Glacier fork."""

    pass


class GrayGlacier(ArrowGlacier, solc_name="london", ignore=True):
    """Gray Glacier fork."""

    pass


class Paris(
    London,
    transition_tool_name="Merge",
):
    """Paris (Merge) fork."""

    @classmethod
    def header_prev_randao_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Prev Randao is required starting from Paris."""
        del block_number, timestamp
        return True

    @classmethod
    def header_zero_difficulty_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Zero difficulty is required starting from Paris."""
        del block_number, timestamp
        return True

    @classmethod
    def get_reward(cls, *, block_number: int = 0, timestamp: int = 0) -> int:
        """Paris updates the reward to 0."""
        del block_number, timestamp
        return 0

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Paris, payloads can be sent through the engine API."""
        del block_number, timestamp
        return 1


class Shanghai(Paris):
    """Shanghai fork."""

    @classmethod
    def header_withdrawals_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Withdrawals are required starting from Shanghai."""
        del block_number, timestamp
        return True

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Shanghai, new payload calls must use version 2."""
        del block_number, timestamp
        return 2

    @classmethod
    def max_initcode_size(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """From Shanghai, the initcode size is now limited. See EIP-3860."""
        del block_number, timestamp
        return 0xC000

    @classmethod
    def _calculate_create_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CREATE gas cost based on metadata (from Shanghai, includes
        initcode cost).
        """
        metadata = opcode.metadata

        # Get base cost from parent fork
        base_cost = super(Shanghai, cls)._calculate_create_gas(
            opcode, gas_costs
        )

        # Add initcode cost (EIP-3860)
        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        init_code_gas = gas_costs.G_INITCODE_WORD * init_code_words

        return base_cost + init_code_gas

    @classmethod
    def _calculate_create2_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        Calculate CREATE2 gas cost based on metadata (from Shanghai,
        includes initcode cost).
        """
        metadata = opcode.metadata

        # Get base cost from parent fork (includes keccak hash cost)
        base_cost = super(Shanghai, cls)._calculate_create2_gas(
            opcode, gas_costs
        )

        # Add initcode cost (EIP-3860)
        init_code_size = metadata["init_code_size"]
        init_code_words = (init_code_size + 31) // 32
        init_code_gas = gas_costs.G_INITCODE_WORD * init_code_words

        return base_cost + init_code_gas

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add Shanghai opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Shanghai, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.PUSH0: gas_costs.G_BASE,
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [Opcodes.PUSH0] + super(Shanghai, cls).valid_opcodes()


class Cancun(Shanghai):
    """Cancun fork."""

    BLOB_CONSTANTS = {  # every value is an int or a Literal
        "FIELD_ELEMENTS_PER_BLOB": 4096,
        "BYTES_PER_FIELD_ELEMENT": 32,
        "CELL_LENGTH": 2048,
        # EIP-2537: Main subgroup order = q, due to this BLS_MODULUS
        # every blob byte (uint256) must be smaller than 116
        "BLS_MODULUS": (
            0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
        ),
        # https://github.com/ethereum/consensus-specs/blob/
        # cc6996c22692d70e41b7a453d925172ee4b719ad/specs/deneb/
        # polynomial-commitments.md?plain=1#L78
        "BYTES_PER_PROOF": 48,
        "BYTES_PER_COMMITMENT": 48,
        "KZG_ENDIANNESS": "big",
        "AMOUNT_CELL_PROOFS": 0,
    }

    @classmethod
    def get_blob_constant(cls, name: str) -> int | Literal["big"]:
        """Return blob constant if it exists."""
        retrieved_constant = cls.BLOB_CONSTANTS.get(name)
        assert retrieved_constant is not None, (
            f"You tried to retrieve the blob constant {name} but it does "
            "not exist!"
        )
        return retrieved_constant

    @classmethod
    def header_excess_blob_gas_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Excess blob gas is required starting from Cancun."""
        del block_number, timestamp
        return True

    @classmethod
    def header_blob_gas_used_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Blob gas used is required starting from Cancun."""
        del block_number, timestamp
        return True

    @classmethod
    def header_beacon_root_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Parent beacon block root is required starting from Cancun."""
        del block_number, timestamp
        return True

    @classmethod
    def blob_gas_price_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BlobGasPriceCalculator:
        """Return a callable that calculates the blob gas price at Cancun."""
        min_base_fee_per_blob_gas = cls.min_base_fee_per_blob_gas(
            block_number=block_number, timestamp=timestamp
        )
        blob_base_fee_update_fraction = cls.blob_base_fee_update_fraction(
            block_number=block_number, timestamp=timestamp
        )

        def fn(*, excess_blob_gas: int) -> int:
            return fake_exponential(
                min_base_fee_per_blob_gas,
                excess_blob_gas,
                blob_base_fee_update_fraction,
            )

        return fn

    @classmethod
    def excess_blob_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block at
        Cancun.
        """
        target_blobs_per_block = cls.target_blobs_per_block(
            block_number=block_number, timestamp=timestamp
        )
        blob_gas_per_blob = cls.blob_gas_per_blob(
            block_number=block_number, timestamp=timestamp
        )
        target_blob_gas_per_block = target_blobs_per_block * blob_gas_per_blob

        def fn(
            *,
            parent_excess_blob_gas: int | None = None,
            parent_excess_blobs: int | None = None,
            parent_blob_gas_used: int | None = None,
            parent_blob_count: int | None = None,
            # Required for Osaka as using this as base
            parent_base_fee_per_gas: int,
        ) -> int:
            del parent_base_fee_per_gas

            if parent_excess_blob_gas is None:
                assert parent_excess_blobs is not None, (
                    "Parent excess blobs are required"
                )
                parent_excess_blob_gas = (
                    parent_excess_blobs * blob_gas_per_blob
                )
            if parent_blob_gas_used is None:
                assert parent_blob_count is not None, (
                    "Parent blob count is required"
                )
                parent_blob_gas_used = parent_blob_count * blob_gas_per_blob
            if (
                parent_excess_blob_gas + parent_blob_gas_used
                < target_blob_gas_per_block
            ):
                return 0
            else:
                return (
                    parent_excess_blob_gas
                    + parent_blob_gas_used
                    - target_blob_gas_per_block
                )

        return fn

    @classmethod
    def min_base_fee_per_blob_gas(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the minimum base fee per blob gas for Cancun."""
        del block_number, timestamp
        return 1

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for Cancun."""
        del block_number, timestamp
        return 3338477

    @classmethod
    def blob_gas_per_blob(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs are enabled starting from Cancun."""
        del block_number, timestamp
        return 2**17

    @classmethod
    def supports_blobs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """At Cancun, blobs support is enabled."""
        del block_number, timestamp
        return True

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        Blobs are enabled starting from Cancun, with a static target of 3 blobs
        per block.
        """
        del block_number, timestamp
        return 3

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        Blobs are enabled starting from Cancun, with a static max of 6 blobs
        per block.
        """
        del block_number, timestamp
        return 6

    @classmethod
    def blob_reserve_price_active(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Blob reserve price is not supported in Cancun."""
        del block_number, timestamp
        return False

    @classmethod
    def full_blob_tx_wrapper_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """
        Pre-Osaka forks don't use tx wrapper versions for full blob
        transactions.
        """
        del block_number, timestamp
        return None

    @classmethod
    def max_blobs_per_tx(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        Blobs are enabled starting from Cancun, with a static max equal to the
        max per block.
        """
        return cls.max_blobs_per_block(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def blob_schedule(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> BlobSchedule | None:
        """
        At Cancun, the fork object runs this routine to get the updated blob
        schedule.
        """
        parent_fork = cls.parent()
        assert parent_fork is not None, "Parent fork must be defined"
        blob_schedule = (
            parent_fork.blob_schedule(
                block_number=block_number, timestamp=timestamp
            )
            or BlobSchedule()
        )
        current_blob_schedule = ForkBlobSchedule(
            target_blobs_per_block=cls.target_blobs_per_block(
                block_number=block_number, timestamp=timestamp
            ),
            max_blobs_per_block=cls.max_blobs_per_block(
                block_number=block_number, timestamp=timestamp
            ),
            base_fee_update_fraction=cls.blob_base_fee_update_fraction(
                block_number=block_number, timestamp=timestamp
            ),
        )
        blob_schedule.append(fork=cls.name(), schedule=current_blob_schedule)
        return blob_schedule

    @classmethod
    def tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Cancun, blob type transactions are introduced."""
        return [3] + super(Cancun, cls).tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """At Cancun, a precompile for kzg point evaluation is introduced."""
        return [
            Address(10, label="KZG_POINT_EVALUATION"),
        ] + super(Cancun, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def system_contracts(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """Cancun introduces the system contract for EIP-4788."""
        del block_number, timestamp
        return [
            Address(
                0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02,
                label="BEACON_ROOTS_ADDRESS",
            )
        ]

    @classmethod
    def pre_allocation_blockchain(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Mapping:
        """
        Cancun requires pre-allocation of the beacon root contract for EIP-4788
        on blockchain type tests.
        """
        del block_number, timestamp
        new_allocation = {
            0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02: {
                "nonce": 1,
                "code": "0x3373fffffffffffffffffffffffffffffffffffffffe14604d"
                "57602036146024575f5ffd5b5f35801560495762001fff810690"
                "815414603c575f5ffd5b62001fff01545f5260205ff35b5f5ffd"
                "5b62001fff42064281555f359062001fff015500",
            }
        }
        return new_allocation | super(Cancun, cls).pre_allocation_blockchain()  # type: ignore

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Cancun, new payload calls must use version 3."""
        del block_number, timestamp
        return 3

    @classmethod
    def engine_get_blobs_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """At Cancun, the engine get blobs version is 1."""
        del block_number, timestamp
        return 1

    @classmethod
    def engine_new_payload_blob_hashes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """From Cancun, payloads must have blob hashes."""
        del block_number, timestamp
        return True

    @classmethod
    def engine_new_payload_beacon_root(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """From Cancun, payloads must have a parent beacon block root."""
        del block_number, timestamp
        return True

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas costs for Cancun.

        Adds Cancun-specific opcodes: BLOBHASH, BLOBBASEFEE, TLOAD, TSTORE,
        MCOPY.
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        memory_expansion_calculator = cls.memory_expansion_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )

        # Get parent fork's opcode gas map
        base_map = super(Cancun, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )

        # Add Cancun-specific opcodes
        return {
            **base_map,
            # EIP-4844: Shard Blob Transactions
            Opcodes.BLOBHASH: gas_costs.G_VERY_LOW,
            # EIP-7516: BLOBBASEFEE opcode
            Opcodes.BLOBBASEFEE: gas_costs.G_BASE,
            # EIP-1153: Transient storage opcodes
            Opcodes.TLOAD: gas_costs.G_WARM_SLOAD,
            Opcodes.TSTORE: gas_costs.G_WARM_SLOAD,
            # EIP-5656: MCOPY - Memory copying instruction
            Opcodes.MCOPY: cls._with_memory_expansion(
                cls._with_data_copy(gas_costs.G_VERY_LOW, gas_costs),
                memory_expansion_calculator,
            ),
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [
            Opcodes.BLOBHASH,
            Opcodes.BLOBBASEFEE,
            Opcodes.TLOAD,
            Opcodes.TSTORE,
            Opcodes.MCOPY,
        ] + super(Cancun, cls).valid_opcodes()


class Prague(Cancun):
    """Prague fork."""

    # update some blob constants
    BLOB_CONSTANTS = {
        **Cancun.BLOB_CONSTANTS,  # same base constants as cancun
        "MAX_BLOBS_PER_BLOCK": 9,  # but overwrite or add these
        "TARGET_BLOBS_PER_BLOCK": 6,
        "MAX_BLOB_GAS_PER_BLOCK": 1179648,
        "TARGET_BLOB_GAS_PER_BLOCK": 786432,
        "BLOB_BASE_FEE_UPDATE_FRACTION": 5007716,
    }

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """
        At Prague, precompiles for BLS operations are added.

        BLS12_G1ADD = 0x0B
        BLS12_G1MSM = 0x0C
        BLS12_G2ADD = 0x0D
        BLS12_G2MSM = 0x0E
        BLS12_PAIRING_CHECK = 0x0F
        BLS12_MAP_FP_TO_G1 = 0x10
        BLS12_MAP_FP2_TO_G2 = 0x11
        """
        return [
            Address(11, label="BLS12_G1ADD"),
            Address(12, label="BLS12_G1MSM"),
            Address(13, label="BLS12_G2ADD"),
            Address(14, label="BLS12_G2MSM"),
            Address(15, label="BLS12_PAIRING_CHECK"),
            Address(16, label="BLS12_MAP_FP_TO_G1"),
            Address(17, label="BLS12_MAP_FP2_TO_G2"),
        ] + super(Prague, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def tx_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[int]:
        """At Prague, set-code type transactions are introduced."""
        return [4] + super(Prague, cls).tx_types(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def gas_costs(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> GasCosts:
        """
        On Prague, the standard token cost and the floor token costs are
        introduced due to EIP-7623.
        """
        return replace(
            super(Prague, cls).gas_costs(
                block_number=block_number, timestamp=timestamp
            ),
            G_TX_DATA_STANDARD_TOKEN_COST=4,  # https://eips.ethereum.org/EIPS/eip-7623
            G_TX_DATA_FLOOR_TOKEN_COST=10,
            G_AUTHORIZATION=25_000,
            R_AUTHORIZATION_EXISTING_AUTHORITY=12_500,
        )

    @classmethod
    def system_contracts(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """
        Prague introduces the system contracts for EIP-6110, EIP-7002, EIP-7251
        and EIP-2935.
        """
        return [
            Address(
                0x00000000219AB540356CBB839CBE05303D7705FA,
                label="DEPOSIT_CONTRACT_ADDRESS",
            ),
            Address(
                0x00000961EF480EB55E80D19AD83579A64C007002,
                label="WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS",
            ),
            Address(
                0x0000BBDDC7CE488642FB579F8B00F3A590007251,
                label="CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS",
            ),
            Address(
                0x0000F90827F1C53A10CB7A02335B175320002935,
                label="HISTORY_STORAGE_ADDRESS",
            ),
        ] + super(Prague, cls).system_contracts(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def max_request_type(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        At Prague, three request types are introduced, hence the max request
        type is 2.
        """
        del block_number, timestamp
        return 2

    @classmethod
    def calldata_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> CalldataGasCalculator:
        """
        Return a callable that calculates the transaction gas cost for its
        calldata depending on its contents.
        """
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(*, data: BytesConvertible, floor: bool = False) -> int:
            tokens = 0
            for b in Bytes(data):
                if b == 0:
                    tokens += 1
                else:
                    tokens += 4
            if floor:
                return tokens * gas_costs.G_TX_DATA_FLOOR_TOKEN_COST
            return tokens * gas_costs.G_TX_DATA_STANDARD_TOKEN_COST

        return fn

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        At Prague, the call gas cost needs to take the authorization into
        account.
        """
        metadata = opcode.metadata

        base_cost = super(Prague, cls)._calculate_call_gas(opcode, gas_costs)

        if metadata["delegated_address"] or metadata["delegated_address_warm"]:
            if metadata["delegated_address_warm"]:
                base_cost += gas_costs.G_WARM_ACCOUNT_ACCESS
            else:
                base_cost += gas_costs.G_COLD_ACCOUNT_ACCESS

        return base_cost

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionDataFloorCostCalculator:
        """
        On Prague, due to EIP-7623, the transaction data floor cost is
        introduced.
        """
        calldata_gas_calculator = cls.calldata_gas_calculator(
            block_number=block_number, timestamp=timestamp
        )
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )

        def fn(*, data: BytesConvertible) -> int:
            return (
                calldata_gas_calculator(data=data, floor=True)
                + gas_costs.G_TRANSACTION
            )

        return fn

    @classmethod
    def transaction_intrinsic_cost_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> TransactionIntrinsicCostCalculator:
        """
        At Prague, the transaction intrinsic cost needs to take the
        authorizations into account.
        """
        super_fn = super(Prague, cls).transaction_intrinsic_cost_calculator(
            block_number=block_number, timestamp=timestamp
        )
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        transaction_data_floor_cost_calculator = (
            cls.transaction_data_floor_cost_calculator(
                block_number=block_number, timestamp=timestamp
            )
        )

        def fn(
            *,
            calldata: BytesConvertible = b"",
            contract_creation: bool = False,
            access_list: List[AccessList] | None = None,
            authorization_list_or_count: Sized | int | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            intrinsic_cost: int = super_fn(
                calldata=calldata,
                contract_creation=contract_creation,
                access_list=access_list,
                return_cost_deducted_prior_execution=False,
            )
            if authorization_list_or_count is not None:
                if isinstance(authorization_list_or_count, Sized):
                    authorization_list_or_count = len(
                        authorization_list_or_count
                    )
                intrinsic_cost += (
                    authorization_list_or_count * gas_costs.G_AUTHORIZATION
                )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            transaction_floor_data_cost = (
                transaction_data_floor_cost_calculator(data=calldata)
            )
            return max(intrinsic_cost, transaction_floor_data_cost)

        return fn

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for Prague."""
        del block_number, timestamp
        return 5007716

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in Prague, have a static target of 6 blobs per block."""
        del block_number, timestamp
        return 6

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in Prague, have a static max of 9 blobs per block."""
        del block_number, timestamp
        return 9

    @classmethod
    def pre_allocation_blockchain(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Mapping:
        """
        Prague requires pre-allocation of the beacon chain deposit contract for
        EIP-6110, the exits contract for EIP-7002, and the history storage
        contract for EIP-2935.
        """
        del block_number, timestamp
        new_allocation = {}

        # Add the beacon chain deposit contract
        deposit_contract_tree_depth = 32
        storage = {}
        next_hash = sha256(b"\x00" * 64).digest()
        for i in range(
            deposit_contract_tree_depth + 2,
            deposit_contract_tree_depth * 2 + 1,
        ):
            storage[i] = next_hash
            next_hash = sha256(next_hash + next_hash).digest()

        with open(
            CURRENT_FOLDER / "contracts" / "deposit_contract.bin", mode="rb"
        ) as f:
            new_allocation.update(
                {
                    0x00000000219AB540356CBB839CBE05303D7705FA: {
                        "nonce": 1,
                        "code": f.read(),
                        "storage": storage,
                    }
                }
            )

        # EIP-7002: Add the withdrawal request contract
        with open(
            CURRENT_FOLDER / "contracts" / "withdrawal_request.bin", mode="rb"
        ) as f:
            new_allocation.update(
                {
                    0x00000961EF480EB55E80D19AD83579A64C007002: {
                        "nonce": 1,
                        "code": f.read(),
                    },
                }
            )

        # EIP-7251: Add the consolidation request contract
        with open(
            CURRENT_FOLDER / "contracts" / "consolidation_request.bin",
            mode="rb",
        ) as f:
            new_allocation.update(
                {
                    0x0000BBDDC7CE488642FB579F8B00F3A590007251: {
                        "nonce": 1,
                        "code": f.read(),
                    },
                }
            )

        # EIP-2935: Add the history storage contract
        with open(
            CURRENT_FOLDER / "contracts" / "history_contract.bin", mode="rb"
        ) as f:
            new_allocation.update(
                {
                    0x0000F90827F1C53A10CB7A02335B175320002935: {
                        "nonce": 1,
                        "code": f.read(),
                    }
                }
            )

        return new_allocation | super(Prague, cls).pre_allocation_blockchain()  # type: ignore

    @classmethod
    def header_requests_required(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """
        Prague requires that the execution layer header contains the beacon
        chain requests hash.
        """
        del block_number, timestamp
        return True

    @classmethod
    def engine_new_payload_requests(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """
        From Prague, new payloads include the requests hash as a parameter.
        """
        del block_number, timestamp
        return True

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Prague, new payload calls must use version 4."""
        del block_number, timestamp
        return 4

    @classmethod
    def engine_forkchoice_updated_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        At Prague, version number of NewPayload and ForkchoiceUpdated diverge.
        """
        del block_number, timestamp
        return 3


class Osaka(Prague, solc_name="cancun"):
    """Osaka fork."""

    # update some blob constants
    BLOB_CONSTANTS = {
        **Prague.BLOB_CONSTANTS,  # same base constants as prague
        "AMOUNT_CELL_PROOFS": 128,
    }

    @classmethod
    def engine_get_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Osaka, get payload calls must use version 5."""
        del block_number, timestamp
        return 5

    @classmethod
    def engine_get_blobs_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """At Osaka, the engine get blobs version is 2."""
        del block_number, timestamp
        return 2

    @classmethod
    def full_blob_tx_wrapper_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """At Osaka, the full blob transaction wrapper version is defined."""
        del block_number, timestamp
        return 1

    @classmethod
    def transaction_gas_limit_cap(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """At Osaka, transaction gas limit is capped at 16 million (2**24)."""
        del block_number, timestamp
        return 16_777_216

    @classmethod
    def block_rlp_size_limit(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """From Osaka, block RLP size is limited as specified in EIP-7934."""
        del block_number, timestamp

        max_block_size = 10_485_760
        safety_margin = 2_097_152
        return max_block_size - safety_margin

    @classmethod
    def opcode_gas_map(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add Osaka opcodes gas costs."""
        gas_costs = cls.gas_costs(
            block_number=block_number, timestamp=timestamp
        )
        base_map = super(Osaka, cls).opcode_gas_map(
            block_number=block_number, timestamp=timestamp
        )
        return {
            **base_map,
            Opcodes.CLZ: gas_costs.G_LOW,
        }

    @classmethod
    def valid_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        del block_number, timestamp
        return [
            Opcodes.CLZ,
        ] + super(Prague, cls).valid_opcodes()

    @classmethod
    def precompiles(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Address]:
        """
        At Osaka, a precompile for p256verify operation is added.

        P256VERIFY = 0x100
        """
        return [
            Address(0x100, label="P256VERIFY"),
        ] + super(Osaka, cls).precompiles(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def excess_blob_gas_calculator(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block.
        """
        target_blobs_per_block = cls.target_blobs_per_block(
            block_number=block_number, timestamp=timestamp
        )
        blob_gas_per_blob = cls.blob_gas_per_blob(
            block_number=block_number, timestamp=timestamp
        )
        target_blob_gas_per_block = target_blobs_per_block * blob_gas_per_blob
        max_blobs_per_block = cls.max_blobs_per_block(
            block_number=block_number, timestamp=timestamp
        )
        blob_base_cost = 2**13  # EIP-7918 new parameter

        def fn(
            *,
            parent_excess_blob_gas: int | None = None,
            parent_excess_blobs: int | None = None,
            parent_blob_gas_used: int | None = None,
            parent_blob_count: int | None = None,
            parent_base_fee_per_gas: int,  # EIP-7918 additional parameter
        ) -> int:
            if parent_excess_blob_gas is None:
                assert parent_excess_blobs is not None, (
                    "Parent excess blobs are required"
                )
                parent_excess_blob_gas = (
                    parent_excess_blobs * blob_gas_per_blob
                )
            if parent_blob_gas_used is None:
                assert parent_blob_count is not None, (
                    "Parent blob count is required"
                )
                parent_blob_gas_used = parent_blob_count * blob_gas_per_blob
            if (
                parent_excess_blob_gas + parent_blob_gas_used
                < target_blob_gas_per_block
            ):
                return 0

            # EIP-7918: Apply reserve price when execution costs dominate blob
            # costs
            current_blob_base_fee = cls.blob_gas_price_calculator()(
                excess_blob_gas=parent_excess_blob_gas
            )
            reserve_price_active = (
                blob_base_cost * parent_base_fee_per_gas
                > blob_gas_per_blob * current_blob_base_fee
            )
            if reserve_price_active:
                blob_excess_adjustment = (
                    parent_blob_gas_used
                    * (max_blobs_per_block - target_blobs_per_block)
                    // max_blobs_per_block
                )
                return parent_excess_blob_gas + blob_excess_adjustment

            # Original EIP-4844 calculation
            return (
                parent_excess_blob_gas
                + parent_blob_gas_used
                - target_blob_gas_per_block
            )

        return fn

    @classmethod
    def max_blobs_per_tx(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """
        Blobs in Osaka, have a static max of 6 blobs per tx. Differs from the
        max per block.
        """
        del block_number, timestamp
        return 6

    @classmethod
    def blob_reserve_price_active(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> bool:
        """Blob reserve price is supported in Osaka."""
        del block_number, timestamp
        return True

    @classmethod
    def blob_base_cost(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the base cost of a blob at a given fork."""
        del block_number, timestamp
        return 2**13  # EIP-7918 new parameter


class BPO1(Osaka, bpo_fork=True):
    """Mainnet BPO1 fork - Blob Parameter Only fork 1."""

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for BPO1."""
        del block_number, timestamp
        return 8346193

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO1 have a target of 10 blobs per block."""
        del block_number, timestamp
        return 10

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO1 have a max of 15 blobs per block."""
        del block_number, timestamp
        return 15


class BPO2(BPO1, bpo_fork=True):
    """Mainnet BPO2 fork - Blob Parameter Only fork 2."""

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for BPO2."""
        del block_number, timestamp
        return 11684671

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO2 have a target of 14 blobs per block."""
        del block_number, timestamp
        return 14

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO2 have a max of 21 blobs per block."""
        del block_number, timestamp
        return 21


class BPO3(BPO2, bpo_fork=True):
    """
    Pseudo BPO3 fork - Blob Parameter Only fork 3.
    For testing purposes only.
    """

    @classmethod
    def is_deployed(cls) -> bool:
        """BPO3 is a pseudo fork for testing, not deployed to mainnet."""
        return False

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for BPO3."""
        del block_number, timestamp
        return 20609697

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO3 have a target of 21 blobs per block."""
        del block_number, timestamp
        return 21

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO3 have a max of 32 blobs per block."""
        del block_number, timestamp
        return 32


class BPO4(BPO3, bpo_fork=True):
    """
    Pseudo BPO4 fork - Blob Parameter Only fork 4.
    For testing purposes only. Testing a decrease in values from BPO3.
    """

    @classmethod
    def blob_base_fee_update_fraction(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Return the blob base fee update fraction for BPO4."""
        del block_number, timestamp
        return 13739630

    @classmethod
    def target_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO4 have a target of 14 blobs per block."""
        del block_number, timestamp
        return 14

    @classmethod
    def max_blobs_per_block(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int:
        """Blobs in BPO4 have a max of 21 blobs per block."""
        del block_number, timestamp
        return 21


class BPO5(BPO4, bpo_fork=True):
    """
    Pseudo BPO5 fork - Blob Parameter Only fork 5.
    For testing purposes only. Required to parse Fusaka devnet genesis files.
    """

    pass


class Amsterdam(BPO2):
    """Amsterdam fork."""

    # TODO: We may need to adjust which BPO Amsterdam inherits from as the
    #  related Amsterdam specs change over time, and before Amsterdam is
    #  live on mainnet.

    @classmethod
    def is_deployed(cls) -> bool:
        """Return True if this fork is deployed."""
        return False

    @classmethod
    def engine_new_payload_version(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """From Amsterdam, new payload calls must use version 5."""
        del block_number, timestamp
        return 5


class EOFv1(Prague, solc_name="cancun"):
    """EOF fork."""

    @classmethod
    def evm_code_types(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[EVMCodeType]:
        """EOF V1 is supported starting from Osaka."""
        return super(EOFv1, cls).evm_code_types(
            block_number=block_number,
            timestamp=timestamp,
        ) + [EVMCodeType.EOF_V1]

    @classmethod
    def call_opcodes(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """EOF V1 introduces EXTCALL, EXTSTATICCALL, EXTDELEGATECALL."""
        return [
            (Opcodes.EXTCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTSTATICCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTDELEGATECALL, EVMCodeType.EOF_V1),
        ] + super(EOFv1, cls).call_opcodes(
            block_number=block_number, timestamp=timestamp
        )

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Flag that the fork has not been deployed to mainnet; it is under active
        development.
        """
        return False
