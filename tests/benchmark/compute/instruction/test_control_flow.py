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


def test_gas_op(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark GAS instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(attack_block=Op.GAS),
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

    benchmark_test(tx=tx)


def test_jumpi_fallthrough(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMPI instruction with fallthrough."""
    benchmark_test(
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

    benchmark_test(tx=tx)


def test_jumpdests(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMPDEST instruction."""
    benchmark_test(code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST))
