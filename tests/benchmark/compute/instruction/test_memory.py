"""
Benchmark memory instructions.

Supported Opcodes:
- MSTORE
- MSTORE8
- MLOAD
- MSIZE
- MCOPY
"""

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Bytecode,
    ExtCallGenerator,
    JumpLoopGenerator,
    Op,
)


@pytest.mark.repricing(mem_size=1_000)
@pytest.mark.parametrize("mem_size", [0, 1, 1_000, 100_000, 1_000_000])
def test_msize(
    benchmark_test: BenchmarkTestFiller,
    mem_size: int,
) -> None:
    """Benchmark MSIZE instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(
            setup=Op.POP(Op.MLOAD(Op.SELFBALANCE)),
            attack_block=Op.MSIZE,
            contract_balance=mem_size,
        ),
    )


@pytest.mark.repricing(
    offset=31,
    offset_initialized=True,
    big_memory_expansion=True,
)
@pytest.mark.parametrize("opcode", [Op.MLOAD, Op.MSTORE, Op.MSTORE8])
@pytest.mark.parametrize("offset", [0, 1, 31])
@pytest.mark.parametrize("offset_initialized", [True, False])
@pytest.mark.parametrize("big_memory_expansion", [True, False])
def test_memory_access(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    offset: int,
    offset_initialized: bool,
    big_memory_expansion: bool,
) -> None:
    """Benchmark memory access instructions."""
    mem_exp_code = (
        Op.MSTORE8(10 * 1024, 1) if big_memory_expansion else Bytecode()
    )
    offset_set_code = (
        Op.MSTORE(offset, 43) if offset_initialized else Bytecode()
    )
    setup = mem_exp_code + offset_set_code + Op.PUSH1(42) + Op.PUSH1(offset)

    attack_block = (
        Op.POP(Op.MLOAD(Op.DUP1))
        if opcode == Op.MLOAD
        else opcode(Op.DUP2, Op.DUP2)
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ),
    )


@pytest.mark.repricing(size=10 * 1024, fixed_src_dst=True)
@pytest.mark.parametrize(
    "size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(100, id="100 bytes"),
        pytest.param(10 * 1024, id="10KiB"),
        pytest.param(1024 * 1024, id="1MiB"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_mcopy(
    benchmark_test: BenchmarkTestFiller,
    size: int,
    fixed_src_dst: bool,
) -> None:
    """Benchmark MCOPY instruction."""
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.MCOPY(src_dst, src_dst, size)

    mem_touch = (
        Op.MSTORE8(0, Op.GAS)
        + Op.MSTORE8(size // 2, Op.GAS)
        + Op.MSTORE8(size - 1, Op.GAS)
        if size > 0
        else Bytecode()
    )
    benchmark_test(
        code_generator=JumpLoopGenerator(
            attack_block=attack_block, cleanup=mem_touch
        ),
    )
