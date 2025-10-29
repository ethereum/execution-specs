"""Benchmark stack instructions."""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    ExtCallGenerator,
    Fork,
    JumpLoopGenerator,
    Op,
)

# Stack instructions:
# POP, PUSHx, DUPx, SWAPx


@pytest.mark.parametrize(
    "opcode",
    [
        Op.SWAP1,
        Op.SWAP2,
        Op.SWAP3,
        Op.SWAP4,
        Op.SWAP5,
        Op.SWAP6,
        Op.SWAP7,
        Op.SWAP8,
        Op.SWAP9,
        Op.SWAP10,
        Op.SWAP11,
        Op.SWAP12,
        Op.SWAP13,
        Op.SWAP14,
        Op.SWAP15,
        Op.SWAP16,
    ],
)
def test_swap(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark SWAP instruction."""
    benchmark_test(
        code_generator=JumpLoopGenerator(
            attack_block=opcode, setup=Op.PUSH0 * opcode.min_stack_height
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.DUP1),
        pytest.param(Op.DUP2),
        pytest.param(Op.DUP3),
        pytest.param(Op.DUP4),
        pytest.param(Op.DUP5),
        pytest.param(Op.DUP6),
        pytest.param(Op.DUP7),
        pytest.param(Op.DUP8),
        pytest.param(Op.DUP9),
        pytest.param(Op.DUP10),
        pytest.param(Op.DUP11),
        pytest.param(Op.DUP12),
        pytest.param(Op.DUP13),
        pytest.param(Op.DUP14),
        pytest.param(Op.DUP15),
        pytest.param(Op.DUP16),
    ],
)
def test_dup(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
) -> None:
    """Benchmark DUP instruction."""
    max_stack_height = fork.max_stack_height()

    min_stack_height = opcode.min_stack_height
    code = Op.PUSH0 * min_stack_height + opcode * (
        max_stack_height - min_stack_height
    )
    target_contract_address = pre.deploy_contract(code=code)

    attack_block = Op.POP(
        Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0)
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(attack_block=attack_block),
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.PUSH0),
        pytest.param(Op.PUSH1),
        pytest.param(Op.PUSH2),
        pytest.param(Op.PUSH3),
        pytest.param(Op.PUSH4),
        pytest.param(Op.PUSH5),
        pytest.param(Op.PUSH6),
        pytest.param(Op.PUSH7),
        pytest.param(Op.PUSH8),
        pytest.param(Op.PUSH9),
        pytest.param(Op.PUSH10),
        pytest.param(Op.PUSH11),
        pytest.param(Op.PUSH12),
        pytest.param(Op.PUSH13),
        pytest.param(Op.PUSH14),
        pytest.param(Op.PUSH15),
        pytest.param(Op.PUSH16),
        pytest.param(Op.PUSH17),
        pytest.param(Op.PUSH18),
        pytest.param(Op.PUSH19),
        pytest.param(Op.PUSH20),
        pytest.param(Op.PUSH21),
        pytest.param(Op.PUSH22),
        pytest.param(Op.PUSH23),
        pytest.param(Op.PUSH24),
        pytest.param(Op.PUSH25),
        pytest.param(Op.PUSH26),
        pytest.param(Op.PUSH27),
        pytest.param(Op.PUSH28),
        pytest.param(Op.PUSH29),
        pytest.param(Op.PUSH30),
        pytest.param(Op.PUSH31),
        pytest.param(Op.PUSH32),
    ],
)
def test_push(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark PUSH instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=opcode[1] if opcode.has_data_portion() else opcode
        ),
    )
