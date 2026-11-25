"""
Benchmark comparison instructions.

Supported Opcodes:
- LT
- SLT
- GT
- SGT
- EQ
- ISZERO
"""

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    JumpLoopGenerator,
    Op,
)


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode,opcode_args",
    [
        (
            Op.LT,  # Keeps getting result 1.
            (0, 1),
        ),
        (
            Op.GT,  # Keeps getting result 0.
            (0, 1),
        ),
        # Operands of the same sign: with different signs the result is the
        # sign of the first operand, which implementations take without
        # comparing the words.
        (
            Op.SLT,  # Keeps getting result 1.
            (0, 1),
        ),
        (
            Op.SGT,  # Keeps getting result 0.
            (0, 1),
        ),
        (
            # The worst case is if the arguments are equal (no early return),
            # so let's keep it comparing ones.
            Op.EQ,
            (1, 1),
        ),
    ],
    ids=lambda param: "" if isinstance(param, tuple) else param,
)
def test_comparison(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    opcode_args: tuple[int, int],
) -> None:
    """
    Benchmark binary instructions (takes two args, pushes one value).

    Each comparison takes the first argument from a PUSH31 and the previous
    result as the second. Clients copy a pushed value out of the code,
    which is slower than duplicating a stack item, and 31 bytes is the
    slowest push size in some of them.
    """
    first, second = opcode_args
    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH1(second),
            attack_block=Op.PUSH31[first.to_bytes(31, "big")] + opcode,
        ),
    )


@pytest.mark.repricing
def test_iszero(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """
    Benchmark ISZERO instruction (takes one arg, pushes one value).
    """
    benchmark_test(
        target_opcode=Op.ISZERO,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH0,
            attack_block=Op.ISZERO,
        ),
    )
