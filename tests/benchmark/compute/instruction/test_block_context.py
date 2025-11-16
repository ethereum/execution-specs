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
@pytest.mark.blockchain_test_no_engine_x
@pytest.mark.parametrize(
    "index,chain_length",
    [
        pytest.param(0, 256, id="genesis"),
        pytest.param(1, 256, id="block_1"),
        pytest.param(256, 256, id="block_256"),
        pytest.param(257, 256, id="current_block"),
        pytest.param(None, 256, id="random"),
    ],
)
@pytest.mark.slow("Generates long chain")
@pytest.mark.skip("Blocks release generation")
def test_blockhash(
    benchmark_test: BenchmarkTestFiller,
    index: int | None,
    chain_length: int,
) -> None:
    """
    Benchmark BLOCKHASH instruction accessing oldest allowed block.

    Note: This test is excluded from engine x format generation because it
    creates 256 empty blocks which are particularly slow to process in
    pre-allocation grouping mode. The test still generates blockchain_test and
    blockchain_test_engine formats which are sufficient for benchmarking
    purposes.
    """
    # Create 256 dummy blocks to fill the blockhash window.
    blocks = [Block()] * 256
    """Benchmark BLOCKHASH instruction accessing oldest allowed block."""
    # Create `chain_length` dummy blocks to fill the blockhash window.
    blocks = [Block()] * chain_length

    block_number = Op.AND(Op.GAS, 0xFF) if index is None else index

    benchmark_test(
        setup_blocks=blocks,
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOCKHASH(block_number)
        ),
    )
