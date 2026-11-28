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
        # Operands of the same sign: with different signs the result is the
        # sign of the first operand, which implementations take without
        # comparing the words.
        pytest.param(
            Op.SLT,  # Keeps getting result 1.
            (0, 1),
            id="opcode_SLT-same_sign",
        ),
        pytest.param(
            Op.SGT,  # Keeps getting result 0.
            (0, 1),
            id="opcode_SGT-same_sign",
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
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={"data": tx_data},
        ),
    )


def random_operand(signed: bool, rng: random.Random) -> int:
    """
    Return a value whose highest nonzero 64-bit word is random (or none,
    giving 0 or 1), with a random sign for the signed comparisons.
    """
    top = rng.randrange(-1, 4)
    if top < 0:
        value = rng.getrandbits(1)
    else:
        value = rng.getrandbits(64 * top) | (rng.getrandbits(64) | 1) << (
            64 * top
        )
    if signed and rng.getrandbits(1):
        value |= 1 << 255
    return value


def random_operand_pair(signed: bool, rng: random.Random) -> tuple[int, int]:
    """
    Return two values equal above a random 64-bit word and different in
    it, in random order, so the result and the deciding word are random.
    For the signed comparisons, the signs are random as well.
    """
    word = rng.randrange(4)
    a = rng.getrandbits(256)
    low_mask = (1 << (64 * (word + 1))) - 1
    b = (a & ~low_mask) | rng.getrandbits(64 * (word + 1))
    if rng.getrandbits(1):
        b = a  # Equal operands: EQ is true, no word decides the order.
    if signed and rng.getrandbits(1):
        b ^= 1 << 255
    return a, b


@pytest.mark.parametrize("opcode", [Op.LT, Op.GT, Op.SLT, Op.SGT, Op.EQ])
@pytest.mark.parametrize("operands", ["chain", "pair"])
def test_comparison_random_operands(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    operands: str,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark comparison instructions with operands that vary from one
    comparison to the next.

    `chain` compares a pushed constant with the previous result, so each
    comparison waits for the previous one. `pair` compares two pushed
    constants. The constants come from a fixed seed and make the result,
    the deciding 64-bit word and, for SLT and SGT, the signs differ
    between comparisons, so implementations that branch on them cannot
    predict the branches.
    """
    rng = random.Random(1)
    signed = opcode in (Op.SLT, Op.SGT)
    if operands == "chain":
        setup: Bytecode = Op.PUSH0

        def comparison() -> Bytecode:
            return Op.PUSH32(random_operand(signed, rng)) + opcode

    elif operands == "pair":
        setup = Bytecode()

        def comparison() -> Bytecode:
            a, b = random_operand_pair(signed, rng)
            return Op.PUSH32(b) + Op.PUSH32(a) + opcode + Op.POP

    else:
        raise ValueError(f"unknown operands: {operands}")

    jump = Op.JUMP(len(setup))
    body: Bytecode = Op.JUMPDEST
    while True:
        block = comparison()
        if len(setup + body + block + jump) > fork.max_code_size():
            break
        body += block

    tx = Transaction(
        to=pre.deploy_contract(code=setup + body + jump),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )
    benchmark_test(target_opcode=opcode, tx=tx)


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
