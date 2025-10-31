"""Benchmark block context instructions."""

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Block,
    ExtCallGenerator,
    Op,
)

# Block context instructions:
# BLOCKHASH, COINBASE, TIMESTAMP, NUMBER, PREVRANDAO, GASLIMIT, CHAINID,
# BASEFEE, BLOBBASEFEE


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


def test_blockhash(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark BLOCKHASH instruction accessing oldest allowed block."""
    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256

    benchmark_test(
        setup_blocks=blocks,
        code_generator=ExtCallGenerator(attack_block=Op.BLOCKHASH(1)),
    )
