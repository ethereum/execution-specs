"""Benchmark block instructions."""

import pytest
from ethereum_test_tools import (
    BenchmarkTestFiller,
    Block,
    ExtCallGenerator,
)
from ethereum_test_vm import Opcodes as Op

# Block instructions:
# BLOCKHASH, COINBASE, TIMESTAMP, NUMBER, PREVRANDAO, GASLIMIT, CHAINID


@pytest.mark.parametrize(
    "opcode",
    [
        Op.COINBASE,
        Op.TIMESTAMP,
        Op.NUMBER,
        Op.PREVRANDAO,
        Op.GASLIMIT,
        Op.CHAINID,
    ],
)
def test_block_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark block zero-parameter instructions."""
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
