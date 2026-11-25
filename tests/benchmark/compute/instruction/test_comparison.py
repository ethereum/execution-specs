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

import random

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    JumpLoopGenerator,
    Op,
    Transaction,
)


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode,opcode_args",
    [
        (
            Op.LT,  # Keeps getting result 1.
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
def test_gt(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Benchmark GT instruction with unpredictable results.

    Each GT takes the first argument from a PUSH31 and the previous result
    as the second, as in the other comparison benchmarks. The pushed values
    make the results a random sequence of zeros and ones.
    """
    rng = random.Random(1)  # Use random with a fixed seed.
    setup = Op.PUSH1(1)
    loop_back = Op.JUMP(len(setup))
    room = fork.max_code_size() - len(setup + Op.JUMPDEST + loop_back)
    count = room // len(Op.PUSH31[bytes(31)] + Op.GT)
    # The last result is 1, as the setup's, so every loop pass is the same.
    results = [rng.getrandbits(1) for _ in range(count - 1)] + [1]

    body = Bytecode(Op.JUMPDEST)
    previous = 1
    for result in results:
        # GT(previous + result, previous) is result.
        body += Op.PUSH31[(previous + result).to_bytes(31, "big")] + Op.GT
        previous = result

    code = setup + body + loop_back
    benchmark_test(
        target_opcode=Op.GT,
        tx=Transaction(
            to=pre.deploy_contract(code=code), sender=pre.fund_eoa()
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
