"""Helper functions for the EVM benchmark worst-case tests."""

import math
from enum import Enum, auto
from typing import Sequence, cast

from execution_testing import Fork, Hash, Op

from tests.osaka.eip7951_p256verify_precompiles.spec import (
    BytesConcatenation as P256BytesConcatenation,
)
from tests.osaka.eip7951_p256verify_precompiles.spec import (
    FieldElement,
)
from tests.prague.eip2537_bls_12_381_precompiles.spec import (
    BytesConcatenation as BLSBytesConcatenation,
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
    """Helper enum to specify return data is returned to the caller."""

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
        Sequence[str]
        | Sequence[P256BytesConcatenation]
        | Sequence[BLSBytesConcatenation]
        | Sequence[bytes]
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
                P256BytesConcatenation,
                BLSBytesConcatenation,
                FieldElement,
            ),
        )
        for p in parameters
    ):
        parameters_bytes_list = [
            bytes(p)
            for p in cast(
                Sequence[
                    P256BytesConcatenation
                    | BLSBytesConcatenation
                    | bytes
                    | FieldElement
                ],
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
