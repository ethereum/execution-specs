"""
Tests benchmark worst-case opcode scenarios.
"""

import pytest
from ethereum_test_benchmark.benchmark_code_generator import JumpLoopGenerator
from ethereum_test_tools import (
    BenchmarkTestFiller,
    Bytecode,
)
from ethereum_test_vm import Opcode
from ethereum_test_vm import Opcodes as Op


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.LOG0, id="log0"),
        pytest.param(Op.LOG1, id="log1"),
        pytest.param(Op.LOG2, id="log2"),
        pytest.param(Op.LOG3, id="log3"),
        pytest.param(Op.LOG4, id="log4"),
    ],
)
@pytest.mark.parametrize(
    "size,non_zero_data",
    [
        pytest.param(0, False, id="0_bytes_data"),
        pytest.param(1024 * 1024, False, id="1_MiB_zeros_data"),  # 1 MiB
        pytest.param(1024 * 1024, True, id="1_MiB_non_zero_data"),  # 1 MiB
    ],
)
@pytest.mark.parametrize(
    "zeros_topic",
    [
        pytest.param(True, id="zeros_topic"),
        pytest.param(False, id="non_zero_topic"),
    ],
)
@pytest.mark.parametrize("fixed_offset", [True, False])
def test_worst_log_opcodes(
    benchmark_test: BenchmarkTestFiller,
    opcode: Opcode,
    zeros_topic: bool,
    size: int,
    fixed_offset: bool,
    non_zero_data: bool,
) -> None:
    """Test running a block with as many LOG opcodes as possible."""
    setup = Bytecode()

    # For non-zero data, load  into memory.
    if non_zero_data:
        setup += Op.CODECOPY(dest_offset=0, offset=0, size=Op.CODESIZE)

    # Push the size value onto the stack and access it using the DUP opcode.
    setup += Op.PUSH3(size)

    # For non-zeros topic, push a non-zero value for topic.
    setup += Op.PUSH0 if zeros_topic else Op.PUSH32(2**256 - 1)

    topic_count = len(opcode.kwargs or []) - 2
    offset = Op.PUSH0 if fixed_offset else Op.MOD(Op.GAS, 7)

    # Calculate the appropriate DUP opcode based on topic count
    # 0 topics -> DUP1, 1 topic -> DUP2, N topics -> DUP(N+1)
    size_op = getattr(Op, f"DUP{topic_count + 2}")

    attack_block = Op.DUP1 * topic_count + size_op + offset + opcode

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ),
    )
