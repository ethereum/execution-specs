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
    Alloc,
    BenchmarkCodeGenerator,
    BenchmarkTestFiller,
    Bytecode,
    Conditional,
    ExtCallGenerator,
    Fork,
    Hash,
    JumpLoopGenerator,
    Op,
    Transaction,
    WhileGas,
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


@pytest.mark.parametrize("mem_size", [0, 8 * 1024, 64 * 1024])
def test_sibling_frame_memory(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    mem_size: int,
) -> None:
    """Benchmark sibling call frames that each expand their own memory."""
    frame_code = Op.STOP if mem_size == 0 else Op.MSTORE8(mem_size - 1, 0)
    frame_address = pre.deploy_contract(code=frame_code)

    benchmark_test(
        target_opcode=Op.CALL,
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=frame_address,
                )
            )
        ),
    )


@pytest.mark.parametrize("depth", [1, 64, 256])
@pytest.mark.parametrize("mem_size", [0, 8 * 1024, 64 * 1024])
def test_nested_frame_memory(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    depth: int,
    mem_size: int,
) -> None:
    """Benchmark a deep frame stack where every frame holds live memory."""
    leaf_address = pre.deploy_contract(
        code=WhileGas(body=Op.POP(Op.MLOAD(Op.PUSH0)), fork=fork)
    )

    # The frame's own memory is claimed before the descent, and must not
    # overlap memory[0:32], which carries the depth to the next frame.
    frame_memory = (
        Op.MSTORE8(mem_size - 1, 0xFF) if mem_size > 0 else Bytecode()
    )

    descend = Op.MSTORE(0, Op.SUB(Op.CALLDATALOAD(0), 1)) + Op.POP(
        Op.CALL(
            gas=Op.GAS,
            address=Op.ADDRESS,
            args_offset=0,
            args_size=32,
        )
    )

    entry_address = pre.deploy_contract(
        code=frame_memory
        + Conditional(
            condition=Op.ISZERO(Op.CALLDATALOAD(0)),
            if_true=Op.POP(Op.CALL(gas=Op.GAS, address=leaf_address)),
            if_false=descend,
        )
    )

    benchmark_test(
        tx=Transaction(
            to=entry_address,
            data=Hash(depth),
            sender=pre.fund_eoa(),
        ),
        skip_gas_used_validation=True,
    )
