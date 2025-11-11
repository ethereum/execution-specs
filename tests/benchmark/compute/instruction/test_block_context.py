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
    TestPhaseManager,
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
    """Benchmark BLOCKHASH instruction accessing oldest allowed block."""
    # Create `chain_length` dummy blocks to fill the blockhash window.
    with TestPhaseManager.setup():
        blocks = [Block()] * chain_length

    block_number = Op.AND(Op.GAS, 0xFF) if index is None else index

    benchmark_test(
        setup_blocks=blocks,
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOCKHASH(block_number)
        ),
    )
