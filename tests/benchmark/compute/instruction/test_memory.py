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
    BenchmarkCodeGenerator,
    BenchmarkTestFiller,
    Bytecode,
    ExtCallGenerator,
    Fork,
    JumpLoopGenerator,
    Op,
)


@pytest.mark.repricing(mem_size=1)
# MSIZE should be O(1), but sweep mem_size so a size-dependent
# implementation shows up as a regression. ExtCallGenerator re-expands
# memory in every call frame, so once the expansion outweighs a frame's
# MSIZE work (~16 KiB), loop in a single frame instead, paying one POP
# per MSIZE but expanding only once.
@pytest.mark.parametrize("mem_size", [0, 1, 1_000, 100_000, 1_000_000])
def test_msize(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    mem_size: int,
) -> None:
    """Benchmark MSIZE instruction."""
    setup = Op.POP(Op.MLOAD(Op.SELFBALANCE))
    expansion_gas = fork.memory_expansion_gas_calculator()(new_bytes=mem_size)
    frame_msize_gas = fork.max_stack_height() * fork.gas_costs().BASE

    code_generator: BenchmarkCodeGenerator
    if expansion_gas <= frame_msize_gas:
        code_generator = ExtCallGenerator(
            setup=setup,
            attack_block=Op.MSIZE,
            contract_balance=mem_size,
        )
    else:
        code_generator = JumpLoopGenerator(
            setup=setup,
            attack_block=Op.POP(Op.MSIZE),
            contract_balance=mem_size,
        )

    benchmark_test(
        target_opcode=Op.MSIZE,
        code_generator=code_generator,
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
    [0, 32, 256, 1024, 10 * 1024, 1024 * 1024],
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
