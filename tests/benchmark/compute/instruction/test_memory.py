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


@pytest.mark.repricing(mem_size=1)
@pytest.mark.parametrize("mem_size", [0, 1, 1_000, 100_000, 1_000_000])
def test_msize(
    benchmark_test: BenchmarkTestFiller,
    mem_size: int,
) -> None:
    """Benchmark MSIZE instruction."""
    benchmark_test(
        target_opcode=Op.MSIZE,
        code_generator=ExtCallGenerator(
            setup=Op.POP(Op.MLOAD(Op.SELFBALANCE)),
            attack_block=Op.MSIZE,
            contract_balance=mem_size,
        ),
    )


@pytest.mark.repricing(offset=0, offset_initialized=True)
@pytest.mark.parametrize("opcode", [Op.MLOAD, Op.MSTORE, Op.MSTORE8])
@pytest.mark.parametrize("offset", [0, 1, 31])
@pytest.mark.parametrize("offset_initialized", [True, False])
@pytest.mark.parametrize("mem_size", [0, 32, 256, 1024, 10 * 1024])
def test_memory_access(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    offset: int,
    offset_initialized: bool,
    mem_size: int,
) -> None:
    """Benchmark memory access instructions."""
    setup = Bytecode()

    setup += Op.MSTORE8(mem_size - 1, 1) if mem_size > 0 else Bytecode()
    setup += Op.MSTORE(offset, 43) if offset_initialized else Bytecode()
    setup += Op.PUSH1(42) + Op.PUSH1(offset)

    attack_block = (
        Op.POP(Op.MLOAD(Op.DUP1))
        if opcode == Op.MLOAD
        else opcode(Op.DUP2, Op.DUP2)
    )

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ),
    )


@pytest.mark.repricing(fixed_src_dst=True)
@pytest.mark.parametrize(
    "mem_size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(32, id="32 bytes"),
        pytest.param(256, id="256 bytes"),
        pytest.param(1024, id="1024 bytes"),
        pytest.param(10 * 1024, id="10KiB"),
        pytest.param(1024 * 1024, id="1MiB"),
    ],
)
@pytest.mark.parametrize("copy_size", [0, 32, 256, 1024])
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_mcopy(
    benchmark_test: BenchmarkTestFiller,
    mem_size: int,
    copy_size: int,
    fixed_src_dst: bool,
) -> None:
    """Benchmark MCOPY instruction."""
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.MCOPY(src_dst, src_dst, copy_size)

    mem_touch = (
        Op.MSTORE8(0, Op.GAS)
        + Op.MSTORE8(mem_size // 2, Op.GAS)
        + Op.MSTORE8(mem_size - 1, Op.GAS)
        if mem_size > 0
        else Bytecode()
    )
    benchmark_test(
        target_opcode=Op.MCOPY,
        code_generator=JumpLoopGenerator(
            attack_block=attack_block, cleanup=mem_touch
        ),
    )
