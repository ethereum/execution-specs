"""
Benchmark stack instructions.

Supported Opcodes:
- POP
- PUSHx
- DUPx
- SWAPx
- DUPN
- SWAPN
- EXCHANGE
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    ExtCallGenerator,
    JumpLoopGenerator,
    Op,
    OpcodeTarget,
)


@pytest.mark.repricing
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
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            attack_block=opcode, setup=Op.PUSH0 * opcode.min_stack_height
        ),
    )


@pytest.mark.repricing
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
    opcode: Op,
) -> None:
    """Benchmark DUP instruction."""
    min_stack_height = opcode.min_stack_height
    benchmark_test(
        target_opcode=opcode,
        code_generator=ExtCallGenerator(
            setup=Op.PUSH0 * min_stack_height,
            attack_block=opcode,
        ),
    )


@pytest.mark.repricing
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
        target_opcode=opcode,
        code_generator=ExtCallGenerator(
            attack_block=opcode[1] if opcode.has_data_portion() else opcode
        ),
    )


@pytest.mark.parametrize(
    "opcode,present_data_bytes",
    [
        pytest.param(Op.PUSH1, 0, id="PUSH1 with no data"),
        pytest.param(Op.PUSH2, 0, id="PUSH2 with no data"),
        pytest.param(Op.PUSH2, 1, id="PUSH2 with half its data"),
        pytest.param(Op.PUSH32, 0, id="PUSH32 with no data"),
        pytest.param(Op.PUSH32, 16, id="PUSH32 with half its data"),
        pytest.param(Op.PUSH32, 31, id="PUSH32 one byte short"),
    ],
)
def test_push_truncated_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    present_data_bytes: int,
) -> None:
    """
    Benchmark a PUSH whose data portion runs past the end of the code.
    """
    target_contract = pre.deploy_contract(
        code=bytes([opcode.int()]) + bytes(present_data_bytes)
    )

    benchmark_test(
        target_opcode=OpcodeTarget(f"{opcode} truncated", Op.STATICCALL),
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=target_contract,
                    args_offset=Op.PUSH0,
                    args_size=Op.PUSH0,
                    ret_offset=Op.PUSH0,
                    ret_size=Op.PUSH0,
                )
            )
        ),
    )


@pytest.mark.repricing
@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "stack_index",
    [17, 107, 235],
    ids=lambda x: f"stack_{x}",
)
def test_dupn(
    benchmark_test: BenchmarkTestFiller,
    stack_index: int,
) -> None:
    """Benchmark DUPN instruction."""
    opcode = Op.DUPN[stack_index]
    benchmark_test(
        target_opcode=Op.DUPN,
        code_generator=ExtCallGenerator(
            setup=Op.PUSH0 * opcode.min_stack_height,
            attack_block=opcode,
        ),
    )


@pytest.mark.repricing
@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "stack_index",
    [17, 107, 235],
    ids=lambda x: f"stack_{x}",
)
def test_swapn(
    benchmark_test: BenchmarkTestFiller,
    stack_index: int,
) -> None:
    """Benchmark SWAPN instruction."""
    opcode = Op.SWAPN[stack_index]
    benchmark_test(
        target_opcode=Op.SWAPN,
        code_generator=JumpLoopGenerator(
            attack_block=opcode, setup=Op.PUSH0 * opcode.min_stack_height
        ),
    )


@pytest.mark.repricing
@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "n,m",
    [
        pytest.param(1, 2, id="n_1_m_2"),
        pytest.param(1, 29, id="n_1_m_29"),
        pytest.param(14, 16, id="n_14_m_16"),
    ],
)
def test_exchange(
    benchmark_test: BenchmarkTestFiller,
    n: int,
    m: int,
) -> None:
    """Benchmark EXCHANGE instruction."""
    opcode = Op.EXCHANGE[n, m]
    benchmark_test(
        target_opcode=Op.EXCHANGE,
        code_generator=JumpLoopGenerator(
            attack_block=opcode, setup=Op.PUSH0 * opcode.min_stack_height
        ),
    )
