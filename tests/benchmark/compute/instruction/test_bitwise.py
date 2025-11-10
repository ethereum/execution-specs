"""
Benchmark bitwise instructions.

Supported Opcodes:
- AND
- OR
- XOR
- NOT
- BYTE
- SHL
- SHR
- SAR
- CLZ
"""

import random
from typing import Callable

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

from tests.benchmark.compute.helpers import (
    DEFAULT_BINOP_ARGS,
    make_dup,
    sar,
    shl,
    shr,
)


@pytest.mark.parametrize(
    "opcode,opcode_args",
    [
        (
            Op.AND,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.OR,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.XOR,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.BYTE,  # Keep extracting the last byte: 0x2F.
            (
                31,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
            ),
        ),
        (
            Op.SHL,  # Shift by 1 until getting 0.
            (
                1,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
            ),
        ),
        (
            Op.SHR,  # Shift by 1 until getting 0.
            (
                1,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
            ),
        ),
        (
            Op.SAR,  # Shift by 1 until getting -1.
            (
                1,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
            ),
        ),
    ],
    ids=lambda param: "" if isinstance(param, tuple) else param,
)
def test_bitwise(
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


def test_not_op(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """
    Benchmark NOT instruction (takes one arg, pushes one value).
    """
    benchmark_test(
        code_generator=JumpLoopGenerator(setup=Op.PUSH0, attack_block=Op.NOT),
    )


@pytest.mark.parametrize("shift_right", [Op.SHR, Op.SAR])
def test_shifts(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    shift_right: Op,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark shift instructions with non-trivial arguments.

    This generates left-right pairs of shifts to avoid zeroing the argument.
    Shift amounts are randomly selected from constant pool of 15 stack values.
    """
    max_code_size = fork.max_code_size()

    match shift_right:
        case Op.SHR:
            shift_right_fn = shr
        case Op.SAR:
            shift_right_fn = sar
        case _:
            raise ValueError(f"Unexpected shift op: {shift_right}")

    rng = random.Random(1)  # Use random with a fixed seed.
    initial_value = 2**256 - 1  # The initial value to be shifted; should be
    # negative for SAR.

    # Create the list of shift amounts with 15 elements (max reachable by DUPs
    # instructions). For the worst case keep the values small and omit values
    # divisible by 8.
    shift_amounts = [x + (x >= 8) + (x >= 15) for x in range(1, 16)]

    code_prefix = (
        sum(Op.PUSH1[sh] for sh in shift_amounts)
        + Op.JUMPDEST
        + Op.CALLDATALOAD(0)
    )
    code_suffix = Op.POP + Op.JUMP(len(shift_amounts) * 2)
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)

    def select_shift_amount(
        shift_fn: Callable[[int, int], int], v: int
    ) -> tuple[int, int]:
        """Select a shift amount that will produce a non-zero result."""
        while True:
            index = rng.randint(0, len(shift_amounts) - 1)
            sh = shift_amounts[index]
            new_v = shift_fn(v, sh) % 2**256
            if new_v != 0:
                return new_v, index

    code_body = Bytecode()
    v = initial_value
    while len(code_body) <= code_body_len - 4:
        v, i = select_shift_amount(shl, v)
        code_body += make_dup(len(shift_amounts) - i) + Op.SHL
        v, i = select_shift_amount(shift_right_fn, v)
        code_body += make_dup(len(shift_amounts) - i) + shift_right

    code = code_prefix + code_body + code_suffix
    assert len(code) == max_code_size - 2

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_value.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.valid_from("Osaka")
def test_clz_same(benchmark_test: BenchmarkTestFiller) -> None:
    """Benchmark CLZ instruction with same input."""
    magic_value = 248  # CLZ(248) = 248
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH1(magic_value), attack_block=Op.CLZ
        ),
    )


@pytest.mark.valid_from("Osaka")
def test_clz_diff(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Benchmark CLZ instruction with different input."""
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST
    code_suffix = Op.PUSH0 + Op.JUMP

    available_code_size = max_code_size - len(code_prefix) - len(code_suffix)

    code_seq = Bytecode()

    for i in range(available_code_size):
        value = (2**256 - 1) >> (i % 256)
        clz_op = Op.CLZ(value) + Op.POP
        if len(code_seq) + len(clz_op) > available_code_size:
            break
        code_seq += clz_op

    attack_code = code_prefix + code_seq + code_suffix
    assert len(attack_code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=attack_code),
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)
