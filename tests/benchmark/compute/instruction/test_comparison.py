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
        (
            Op.SLT,  # Keeps getting result 1.
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                1,
            ),
        ),
        (
            Op.SGT,  # Keeps getting result 0.
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                1,
            ),
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
    The execution starts with two initial values on the stack
    The stack is balanced by the DUP2 instruction.
    """
    tx_data = b"".join(
        arg.to_bytes(32, byteorder="big") for arg in opcode_args
    )

    setup = Op.CALLDATALOAD(0) + Op.CALLDATALOAD(32) + Op.DUP2 + Op.DUP2
    attack_block = Op.DUP2 + opcode
    cleanup = Op.POP + Op.POP + Op.DUP2 + Op.DUP2
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={"data": tx_data},
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
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH0,
            attack_block=Op.ISZERO,
        ),
    )
