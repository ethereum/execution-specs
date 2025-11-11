"""
Benchmark block context instructions.

Supported Opcodes:
- BLOCKHASH
- COINBASE
- TIMESTAMP
- NUMBER
- PREVRANDAO
- GASLIMIT
- CHAINID
- BASEFEE
- BLOBBASEFEE
"""

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Block,
    ExtCallGenerator,
    Op,
)


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode",
    [
        Op.COINBASE,
        Op.TIMESTAMP,
        Op.NUMBER,
        Op.PREVRANDAO,
        Op.GASLIMIT,
        Op.CHAINID,
        Op.BASEFEE,
        Op.BLOBBASEFEE,
    ],
)
def test_block_context_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark zero-parameter block context instructions."""
    benchmark_test(
        code_generator=ExtCallGenerator(attack_block=opcode),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "index",
    [
        0,
        1,
        256,
        257,
        pytest.param(None, id="random"),
    ],
)
def test_blockhash(
    benchmark_test: BenchmarkTestFiller,
    index: int | None,
) -> None:
    """Benchmark BLOCKHASH instruction accessing oldest allowed block."""
    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256

    block_number = Op.AND(Op.GAS, 0xFF) if index is None else index

    benchmark_test(
        setup_blocks=blocks,
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOCKHASH(block_number)
        ),
    )
