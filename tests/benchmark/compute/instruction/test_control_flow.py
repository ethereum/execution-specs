"""
Benchmark control flow instructions.

Supported Opcodes:
- STOP
- JUMP
- JUMPI
- PC
- GAS
- JUMPDEST
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    ExtCallGenerator,
    JumpLoopGenerator,
    Op,
    Transaction,
)

# Control flow instructions:
# STOP, JUMP, JUMPI, PC, GAS, JUMPDEST


@pytest.mark.repricing
def test_gas_op(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark GAS instruction."""
    benchmark_test(
        target_opcode=Op.GAS,
        code_generator=ExtCallGenerator(attack_block=Op.GAS),
    )


@pytest.mark.repricing
def test_pc_op(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark PC instruction."""
    benchmark_test(
        target_opcode=Op.PC,
        code_generator=ExtCallGenerator(attack_block=Op.PC),
    )


def test_jumps(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """Benchmark JUMP instruction."""
    tx = Transaction(
        to=pre.deploy_contract(code=(Op.JUMPDEST + Op.JUMP(Op.PUSH0))),
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        target_opcode=Op.JUMP,
        tx=tx,
    )


@pytest.mark.repricing
def test_jump_benchmark(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMP instruction with different dest."""
    benchmark_test(
        target_opcode=Op.JUMP,
        code_generator=JumpLoopGenerator(
            attack_block=Op.JUMP(Op.ADD(Op.PC, 3)) + Op.JUMPDEST
        ),
    )


@pytest.mark.repricing
def test_jumpi_fallthrough(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMPI instruction with fallthrough."""
    benchmark_test(
        target_opcode=Op.JUMPI,
        code_generator=JumpLoopGenerator(
            attack_block=Op.JUMPI(Op.PUSH0, Op.PUSH0)
        ),
    )


def test_jumpis(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """Benchmark JUMPI instruction."""
    tx = Transaction(
        to=pre.deploy_contract(
            code=(Op.JUMPDEST + Op.JUMPI(Op.PUSH0, Op.NUMBER))
        ),
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        target_opcode=Op.JUMPI,
        tx=tx,
    )


@pytest.mark.repricing
def test_jumpdests(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMPDEST instruction."""
    benchmark_test(
        target_opcode=Op.JUMPDEST,
        code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
    )


def test_jump_to_invalid_destination(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """
    Benchmark JUMP instruction targeting an invalid destination.

    A JUMP to a position that is not a JUMPDEST must raise
    InvalidJumpDestError and halt execution. This test verifies
    the error path is exercised correctly under the execution spec.
    """
    tx = Transaction(
        to=pre.deploy_contract(
            code=(
                Op.PUSH1(0x03)  # push invalid destination (not a JUMPDEST)
                + Op.JUMP  # attempt jump — must raise InvalidJumpDestError
            )
        ),
        sender=pre.fund_eoa(),
    )
    benchmark_test(
        target_opcode=Op.JUMP,
        tx=tx,
    )


def test_jumpi_to_invalid_destination(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """
    Benchmark JUMPI instruction targeting an invalid destination.

    A JUMPI with a non-zero condition and a destination that is not a
    JUMPDEST must raise InvalidJumpDestError. This test verifies the
    conditional branch error path under the execution spec.
    """
    tx = Transaction(
        to=pre.deploy_contract(
            code=(
                Op.PUSH1(0x01)  # condition = true (non-zero)
                + Op.PUSH1(0x05)  # invalid destination (not a JUMPDEST)
                + Op.JUMPI  # attempt conditional jump — must raise
            )
        ),
        sender=pre.fund_eoa(),
    )
    benchmark_test(
        target_opcode=Op.JUMPI,
        tx=tx,
    )
