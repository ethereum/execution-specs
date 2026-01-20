"""Helper functions for the EVM benchmark worst-case tests."""

import math
from enum import Enum, auto
from typing import List, Self, Sequence, Type, cast

from execution_testing import (
    EOA,
    Address,
    Alloc,
    Bytecode,
    BytesConcatenation,
    Fork,
    Hash,
    Initcode,
    Op,
    Transaction,
    While,
    compute_create2_address,
    compute_deterministic_create2_address,
)
from execution_testing.vm import ForkOpcodeInterface

from tests.osaka.eip7951_p256verify_precompiles.spec import (
    FieldElement,
)

DEFAULT_BINOP_ARGS = (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001,
)

XOR_TABLE_SIZE = 256
XOR_TABLE = [Hash(i).sha256() for i in range(XOR_TABLE_SIZE)]


class StorageAction:
    """Enum for storage actions."""

    READ = auto()
    WRITE_SAME_VALUE = auto()
    WRITE_NEW_VALUE = auto()


class TransactionResult:
    """Enum for the possible transaction outcomes."""

    SUCCESS = auto()
    OUT_OF_GAS = auto()
    REVERT = auto()


class ReturnDataStyle(Enum):
    """Helper enum to specify how return data is returned to the caller."""

    RETURN = auto()
    REVERT = auto()
    IDENTITY = auto()


class CallDataOrigin:
    """Enum for calldata origins."""

    TRANSACTION = auto()
    CALL = auto()


def neg(x: int) -> int:
    """Negate the given integer in the two's complement 256-bit range."""
    assert 0 <= x < 2**256
    return 2**256 - x


def make_dup(index: int) -> Op:
    """
    Create a DUP instruction which duplicates the index-th (counting from 0)
    element from the top of the stack. E.g. make_dup(0) → DUP1.
    """
    assert 0 <= index < 16, f"DUP index {index} out of range [0, 15]"
    return getattr(Op, f"DUP{index + 1}")


def to_signed(x: int) -> int:
    """Convert an unsigned integer to a signed integer."""
    return x if x < 2**255 else x - 2**256


def to_unsigned(x: int) -> int:
    """Convert a signed integer to an unsigned integer."""
    return x if x >= 0 else x + 2**256


def shr(x: int, s: int) -> int:
    """Shift right."""
    return x >> s


def shl(x: int, s: int) -> int:
    """Shift left."""
    return x << s


def sar(x: int, s: int) -> int:
    """Arithmetic shift right."""
    return to_unsigned(to_signed(x) >> s)


def concatenate_parameters(
    parameters: (
        Sequence[str] | Sequence[BytesConcatenation] | Sequence[bytes]
    ),
) -> bytes:
    """
    Concatenate precompile parameters into bytes.

    Args:
        parameters: List of parameters, either as hex strings or byte objects
                   (bytes, BytesConcatenation, or FieldElement).

    Returns:
        Concatenated bytes from all parameters.

    """
    if all(isinstance(p, str) for p in parameters):
        parameters_str = cast(Sequence[str], parameters)
        concatenated_hex_string = "".join(parameters_str)
        return bytes.fromhex(concatenated_hex_string)
    elif all(
        isinstance(
            p,
            (
                bytes,
                BytesConcatenation,
                FieldElement,
            ),
        )
        for p in parameters
    ):
        parameters_bytes_list = [
            bytes(p)
            for p in cast(
                Sequence[BytesConcatenation | bytes | FieldElement],
                parameters,
            )
        ]
        return b"".join(parameters_bytes_list)
    else:
        raise TypeError(
            "parameters must be a sequence of strings (hex) "
            "or a sequence of byte-like objects (bytes, BytesConcatenation or "
            "FieldElement)."
        )


def calculate_optimal_input_length(
    available_gas: int,
    fork: Fork,
    static_cost: int,
    per_word_dynamic_cost: int,
    bytes_per_unit_of_work: int,
) -> int:
    """
    Calculate the optimal input length to maximize precompile work.

    This function finds the input size that maximizes the total amount of
    work (in terms of bytes processed) a precompile can perform given a
    fixed gas budget. It balances the trade-off between making more calls
    with smaller inputs versus fewer calls with larger inputs.

    Args:
        available_gas: Total gas available for precompile calls.
        fork: The fork to use for gas cost calculations.
        static_cost: Static gas cost per precompile call.
        per_word_dynamic_cost: Dynamic gas cost per 32-byte word of input.
        bytes_per_unit_of_work: Number of bytes processed per unit of work.

    Returns:
        The optimal input length in bytes that maximizes total work.

    """
    gsc = fork.gas_costs()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    max_work = 0
    optimal_input_length = 0

    for input_length in range(1, 1_000_000, 32):
        parameters_gas = (
            gsc.G_BASE  # PUSH0 = arg offset
            + gsc.G_BASE  # PUSH0 = arg size
            + gsc.G_BASE  # PUSH0 = arg size
            + gsc.G_VERY_LOW  # PUSH0 = arg offset
            + gsc.G_VERY_LOW  # PUSHN = address
            + gsc.G_BASE  # GAS
        )
        iteration_gas_cost = (
            parameters_gas
            + static_cost  # Precompile static cost
            + math.ceil(input_length / 32) * per_word_dynamic_cost
            # Precompile dynamic cost
            + gsc.G_BASE  # POP
        )

        # From the available gas, subtract the memory expansion costs
        # considering the current input size length.
        available_gas_after_expansion = max(
            0, available_gas - mem_exp_gas_calculator(new_bytes=input_length)
        )

        # Calculate how many calls we can do.
        num_calls = available_gas_after_expansion // iteration_gas_cost
        total_work = num_calls * math.ceil(
            input_length / bytes_per_unit_of_work
        )

        # If we found an input size with better total work, save it.
        if total_work > max_work:
            max_work = total_work
            optimal_input_length = input_length

    return optimal_input_length


class IteratingBytecode(Bytecode):
    """
    Bytecode composed of distinct execution phases: setup, iteration, and
    cleanup.

    Some phases (warm_iterating and iterating_subcall) are analytical only and
    exist solely to model gas costs; they are not emitted in the final
    bytecode.
    """

    setup: Bytecode
    """Bytecode executed once at the beginning before iterations start."""
    iterating: Bytecode
    """Bytecode executed in the first iteration."""
    warm_iterating: Bytecode
    """
    Analytical bytecode representing subsequent iterations after the first
    (warm state).
    This bytecode is _not_ included in the final bytecode, and it's only
    used for the gas accounting properties of its opcodes and therefore gas
    calculation.
    """
    iterating_subcall: Bytecode
    """
    Analytical bytecode representing a subcall performed during each iteration.
    This bytecode is _not_ included in the final bytecode, and it's only
    used for gas calculation.
    """
    cleanup: Bytecode
    """Bytecode executed once at the end after all iterations complete."""

    def __new__(
        cls,
        *,
        setup: Bytecode,
        iterating: Bytecode,
        cleanup: Bytecode | None = None,
        warm_iterating: Bytecode | None = None,
        iterating_subcall: Bytecode | None = None,
    ) -> Self:
        """
        Create a new iterating bytecode.

        Args:
            setup: Bytecode executed once at the beginning before
                iterations start.
            iterating: Bytecode executed in the first iteration.
            cleanup: Bytecode executed once at the end after all
                iterations complete.
            warm_iterating: Analytical bytecode representing subsequent
                iterations after the first (warm state).
            iterating_subcall: Analytical bytecode representing a subcall
                performed during each iteration. This bytecode is _not_
                included in the final bytecode, and it's only used for gas
                calculation.

        Returns:
            A new IteratingBytecode instance.

        """
        instance = super(IteratingBytecode, cls).__new__(
            cls,
            setup + iterating + cleanup,
        )
        instance.setup = setup
        instance.iterating = iterating
        if warm_iterating is None:
            instance.warm_iterating = iterating
        else:
            assert bytes(iterating) == bytes(warm_iterating), (
                "iterating and warm_iterating must have the same bytecode"
            )
            instance.warm_iterating = warm_iterating
        if iterating_subcall is None:
            instance.iterating_subcall = Bytecode()
        else:
            instance.iterating_subcall = iterating_subcall
        if cleanup is None:
            cleanup = Bytecode()
        instance.cleanup = cleanup
        return instance

    def iterating_subcall_reserve(self, *, fork: Fork) -> int:
        """
        Return the gas reserve needed so that the last iterating subcall does
        not fail due to the 63/64 rule.
        """
        iterating_subcall_gas_cost = self.iterating_subcall.gas_cost(fork=fork)
        return (
            iterating_subcall_gas_cost * 64 // 63
        ) - iterating_subcall_gas_cost

    def gas_cost_by_iteration_count(
        self,
        *,
        fork: Type[ForkOpcodeInterface],
        iteration_count: int,
        block_number: int = 0,
        timestamp: int = 0,
    ) -> int:
        """Return the cost of iterating through the bytecode N times."""
        return (
            self.setup.gas_cost(
                fork=fork, block_number=block_number, timestamp=timestamp
            )
            + self.iterating.gas_cost(
                fork=fork, block_number=block_number, timestamp=timestamp
            )
            + self.warm_iterating.gas_cost(
                fork=fork, block_number=block_number, timestamp=timestamp
            )
            * (iteration_count - 1)
            + (
                self.iterating_subcall.gas_cost(
                    fork=fork, block_number=block_number, timestamp=timestamp
                )
                * iteration_count
            )
            + self.cleanup.gas_cost(
                fork=fork, block_number=block_number, timestamp=timestamp
            )
        )

    def with_fixed_iteration_count(
        self, *, iteration_count: int
    ) -> "FixedIterationsBytecode":
        """
        Return a new FixedIterationsBytecode with the iteration count fixed.
        """
        return FixedIterationsBytecode(
            setup=self.setup,
            iterating=self.iterating,
            cleanup=self.cleanup,
            warm_iterating=self.warm_iterating,
            iterating_subcall=self.iterating_subcall,
            iteration_count=iteration_count,
        )


class FixedIterationsBytecode(IteratingBytecode):
    """
    Bytecode that contains a setup phase, an iterating phase, and a cleanup
    phase, with a fixed number of iterations.

    This type can be used in place of a normal Bytecode and will return the
    appropriate gas cost for the given number of iterations.
    """

    iteration_count: int
    """The fixed number of times the iterating bytecode will be executed."""

    def __new__(
        cls,
        *,
        setup: Bytecode,
        iterating: Bytecode,
        cleanup: Bytecode,
        iteration_count: int,
        warm_iterating: Bytecode | None = None,
        iterating_subcall: Bytecode | None = None,
    ) -> Self:
        """
        Create a new FixedIterationsBytecode instance.

        Args:
            setup: Bytecode executed once at the beginning before
                iterations start.
            iterating: Bytecode executed in the first iteration.
            cleanup: Bytecode executed once at the end after all
                iterations complete.
            iteration_count: The fixed number of times the iterating
                bytecode will be executed.
            warm_iterating: Bytecode executed in subsequent iterations
                after the first. If None, uses the same bytecode as
                iterating.
            iterating_subcall: Analytical bytecode representing a subcall
                performed during each iteration. This bytecode is _not_
                included in the final bytecode, and it's only used for gas
                calculation.

        Returns:
            A new FixedIterationsBytecode instance.

        """
        instance = super(FixedIterationsBytecode, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            cleanup=cleanup,
            warm_iterating=warm_iterating,
            iterating_subcall=iterating_subcall,
        )
        instance.iteration_count = iteration_count
        return instance

    def gas_cost(
        self,
        fork: Type[ForkOpcodeInterface],
        *,
        block_number: int = 0,
        timestamp: int = 0,
    ) -> int:
        """Return the cost of iterating through the bytecode N times."""
        return self.gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=self.iteration_count,
            block_number=block_number,
            timestamp=timestamp,
        )


class MaxSizedContractInitcode(FixedIterationsBytecode):
    """
    Initcode that deploys a random and maximum-sized contract for the given
    fork's limits.
    """

    def __new__(cls, *, pre: Alloc, fork: Fork) -> Self:
        """
        Create a new MaxSizedContractInitcode instance.

        Args:
            pre: The pre-allocation state where the contract will be
                deployed.
            fork: The fork to use for determining maximum contract size
                limits.

        Returns:
            A new MaxSizedContractInitcode instance.

        """
        max_contract_size = fork.max_code_size()
        xor_table_byte_size = XOR_TABLE_SIZE * 32
        iteration_count = ((max_contract_size - 32) // xor_table_byte_size) + 1
        setup = Op.MSTORE(
            0,
            Op.ADDRESS,
            # Gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        iterating = While(
            body=(
                Op.SHA3(Op.SUB(Op.MSIZE, 32), 32, data_size=32)
                # Use a xor table to avoid having to call the "expensive" sha3
                # opcode as much
                + sum(
                    (
                        Op.PUSH32[xor_value]
                        + Op.XOR
                        + Op.DUP1
                        + Op.MSIZE
                        + Op.MSTORE
                    )
                    for xor_value in XOR_TABLE
                )
                + Op.POP
            ),
            condition=Op.LT(Op.MSIZE, max_contract_size),
        )
        cleanup = (
            # Despite the whole contract has random bytecode, we need the first
            # opcode be a STOP so CALL-like attacks return as soon as possible.
            # However, since the memory starts with address, the first 12 bytes
            # are always zero, so no need to do anything but return.
            Op.RETURN(
                0,
                max_contract_size,
                # Gas accounting
                code_deposit_size=max_contract_size,
                # Memory is not expanded here, but it is expanded in the loop.
                old_memory_size=32,
                new_memory_size=(xor_table_byte_size * iteration_count) + 32,
            )
        )
        instance = super(MaxSizedContractInitcode, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            cleanup=cleanup,
            iteration_count=iteration_count,
        )
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance.address(fork=fork)
        return instance

    def address(self, *, fork: Fork) -> Address:
        """Get the deterministic address of the initcode."""
        return compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=self),
            fork=fork,
        )


class MaxSizedContractFactory(IteratingBytecode):
    """
    Factory contract that creates maximum-sized contracts.
    """

    initcode: MaxSizedContractInitcode
    """The initcode used to deploy maximum-sized contracts via CREATE2."""

    def __new__(cls, *, pre: Alloc, fork: Fork) -> Self:
        """
        Create a new MaxSizedContractFactory instance.

        Args:
            pre: The pre-allocation state where the factory will be
                deployed.
            fork: The fork to use for gas calculations and contract
                size limits.

        Returns:
            A new MaxSizedContractFactory instance.

        """
        initcode = MaxSizedContractInitcode(pre=pre, fork=fork)
        initcode_address = initcode.address(fork=fork)
        setup = (
            Op.EXTCODECOPY(
                address=initcode_address,
                dest_offset=0,
                offset=0,
                size=len(initcode),
                # Gas accounting
                address_warm=False,
                data_size=len(initcode),
                new_memory_size=len(initcode),
            )
            + Op.ADD(1, Op.CALLDATALOAD(32))
            + Op.CALLDATALOAD(0)
        )
        iterating = While(
            body=Op.POP(
                Op.CREATE2(
                    value=0,
                    offset=0,
                    size=len(initcode),
                    salt=Op.DUP1,
                    # Gas accounting
                    init_code_size=len(initcode),
                )
            ),
            condition=Op.PUSH1(1)
            + Op.ADD
            + Op.DUP1
            + Op.DUP3
            + Op.LT
            + Op.ISZERO,
        )
        cleanup = Op.STOP
        instance = super(MaxSizedContractFactory, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            iterating_subcall=initcode,
            cleanup=cleanup,
        )
        instance.initcode = initcode
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance.address(fork=fork)
        return instance

    def tx_gas_cost_by_index_range(
        self, *, fork: Fork, index_start: int, index_end: int
    ) -> int:
        """
        Calculate the exact gas cost of a transaction calling the factory
        for a given index range.
        """
        intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
        # Required extra gas for the last iteration due to the 63/64 rule.
        return self.gas_cost_by_iteration_count(
            fork=fork, iteration_count=index_end - index_start + 1
        ) + intrinsic_gas_cost_calc(
            calldata=Hash(index_start) + Hash(index_end)
        )

    def tx_gas_limit_by_index_range(
        self, *, fork: Fork, index_start: int, index_end: int
    ) -> int:
        """Calculate the gas cost of the factory for a given index range."""
        intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
        # Required extra gas for the last iteration due to the 63/64 rule.
        last_iteration_subcall_reserve = self.iterating_subcall_reserve(
            fork=fork
        )
        return (
            self.gas_cost_by_iteration_count(
                fork=fork, iteration_count=index_end - index_start + 1
            )
            + intrinsic_gas_cost_calc(
                calldata=Hash(index_start) + Hash(index_end)
            )
            + last_iteration_subcall_reserve
        )

    def tx(
        self,
        *,
        fork: Fork,
        sender: EOA,
        index_start: int,
        index_end: int,
    ) -> Transaction:
        """
        Create a single transaction calling the factory for a given index
        range.
        """
        return Transaction(
            to=self.address(fork=fork),
            gas_limit=self.tx_gas_limit_by_index_range(
                fork=fork, index_start=index_start, index_end=index_end
            ),
            data=Hash(index_start) + Hash(index_end),
            sender=sender,
        )

    def txs_with_gas_limit_cap(
        self,
        *,
        fork: Fork,
        sender: EOA,
        index_start: int,
        index_end: int,
        gas_limit_cap: int | None,
    ) -> List[Transaction]:
        """
        Create a list of transactions calling the factory for a given index
        range, each capped by the given gas limit cap.
        """
        if gas_limit_cap is None:
            # No limit, deploy everything in a single transaction.
            return [
                self.tx(
                    fork=fork,
                    sender=sender,
                    index_start=index_start,
                    index_end=index_end,
                )
            ]
        # First assert it's possible to deploy a single contract.
        minimum_tx_gas_limit = self.tx_gas_limit_by_index_range(
            fork=fork,
            index_start=index_start,
            index_end=index_start,
        )
        if minimum_tx_gas_limit > gas_limit_cap:
            raise ValueError(
                f"gas limit cap is too low to deploy a single contract: "
                f"{gas_limit_cap} < "
                f"{minimum_tx_gas_limit}"
            )
        current_index_start = index_start
        current_index_end = index_start
        txs = []
        while current_index_end <= index_end:
            # Check if the current range exceeds the gas limit
            if (
                self.tx_gas_limit_by_index_range(
                    fork=fork,
                    index_start=current_index_start,
                    index_end=current_index_end,
                )
                > gas_limit_cap
            ):
                # Create a transaction with the previous range
                txs.append(
                    self.tx(
                        fork=fork,
                        sender=sender,
                        index_start=current_index_start,
                        index_end=current_index_end - 1,
                    )
                )
                # Start a new range
                current_index_start = current_index_end
            current_index_end += 1

        # Handle the last range
        if current_index_start <= index_end:
            txs.append(
                self.tx(
                    fork=fork,
                    sender=sender,
                    index_start=current_index_start,
                    index_end=index_end,
                )
            )

        return txs

    def address(self, *, fork: Fork) -> Address:
        """Get the deterministic address of the initcode."""
        return compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=self),
            fork=fork,
        )

    def created_contract_address(self, *, fork: Fork, salt: int) -> Address:
        """Get the deterministic address of the created contract."""
        return compute_create2_address(
            address=self.address(fork=fork),
            salt=salt,
            initcode=self.initcode,
        )
