"""Helper functions for the EVM benchmark worst-case tests."""

import math
from enum import Enum, auto
from typing import Generator, Self, Sequence, cast

from execution_testing import (
    EOA,
    Address,
    Alloc,
    BytesConcatenation,
    FixedIterationsBytecode,
    Fork,
    Hash,
    Initcode,
    IteratingBytecode,
    Op,
    TransactionWithCost,
    While,
    compute_create2_address,
    compute_deterministic_create2_address,
)

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


class MaxSizedContractInitcode(FixedIterationsBytecode):
    """
    Initcode that deploys a random and maximum-sized contract for the given
    fork's limits.
    """

    _cached_address: Address
    """Cached address to avoid expensive recomputation."""

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
        # Cache the address to avoid expensive recomputation
        instance._cached_address = compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=instance),
            fork=fork,
        )
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance._cached_address
        return instance

    def address(self) -> Address:
        """Get the deterministic address of the initcode."""
        return self._cached_address


class MaxSizedContractFactory(IteratingBytecode):
    """
    Factory contract that creates maximum-sized contracts.

    The contract takes two 32-byte arguments in the calldata:
    - start_index: the starting index of the contract to deploy
    - end_index: the ending index of the contract to deploy

    The contract will deploy a maximum-sized contract for each index in the
    range, inclusive.
    """

    initcode: MaxSizedContractInitcode
    """The initcode used to deploy maximum-sized contracts via CREATE2."""

    _cached_address: Address
    """Cached address to avoid expensive recomputation."""

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
        initcode_address = initcode.address()
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
            # CALLDATA[0:32] = start_index
            # CALLDATA[32:64] = end_index
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
        # Cache the address to avoid expensive recomputation
        instance._cached_address = compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=instance),
            fork=fork,
        )
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance._cached_address
        return instance

    def transactions_by_total_contract_count(
        self,
        *,
        fork: Fork,
        sender: EOA,
        contract_count: int,
        contract_start_index: int = 0,
    ) -> Generator[TransactionWithCost, None, None]:
        """
        Create a list of transactions calling the factory to create the
        given number of contracts, each capped tx properly capped by the
        gas limit cap of the fork.
        """
        to = self.address()

        # Use a sensible hardcoded maximum for the calldata, to avoid
        # binary searching.
        max_number = (2 ** (contract_count.bit_length() + 1)) - 1
        calldata_max = Hash(max_number) + Hash(max_number)

        def calldata(iteration_count: int, start_iteration: int) -> bytes:
            index_end = iteration_count + start_iteration - 1
            return Hash(start_iteration) + Hash(index_end)

        start_iteration: int = contract_start_index

        tx_gas_limit: int | None = None
        tx_gas_cost: int | None = None
        last_iteration_count: int = 0

        for iteration_count in self.tx_iterations_by_total_iteration_count(
            fork=fork,
            total_iterations=contract_count,
            start_iteration=start_iteration,
            calldata=calldata_max,
        ):
            if (
                tx_gas_limit is None
                or tx_gas_cost is None
                or iteration_count != last_iteration_count
            ):
                tx_gas_limit = self.tx_gas_limit_by_iteration_count(
                    fork=fork,
                    iteration_count=iteration_count,
                    start_iteration=start_iteration,
                    calldata=calldata_max,
                )
                tx_gas_cost = self.tx_gas_cost_by_iteration_count(
                    fork=fork,
                    iteration_count=iteration_count,
                    start_iteration=start_iteration,
                    calldata=calldata_max,
                )
            yield TransactionWithCost(
                to=to,
                gas_limit=tx_gas_limit,
                sender=sender,
                gas_cost=tx_gas_cost,
                data=calldata(iteration_count, start_iteration),
            )
            start_iteration += iteration_count
            last_iteration_count = iteration_count

    def address(self) -> Address:
        """Get the deterministic address of the factory contract."""
        return self._cached_address

    def created_contract_address(self, *, salt: int) -> Address:
        """Get the deterministic address of the created contract."""
        return compute_create2_address(
            address=self.address(),
            salt=salt,
            initcode=self.initcode,
        )
