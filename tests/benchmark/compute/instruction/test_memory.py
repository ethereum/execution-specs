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
    Block,
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
    gas_benchmark_value: int,
    tx_gas_limit: int,
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

    descend = Op.MSTORE(0, Op.SUB(Op.CALLDATALOAD(0), 1)) + Conditional(
        condition=Op.CALL(
            gas=Op.GAS,
            address=Op.ADDRESS,
            args_offset=0,
            args_size=32,
            address_warm=True,
        ),
        if_false=Op.REVERT(0, 0),
    )

    frame_code = frame_memory + Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.POP(Op.CALL(gas=Op.GAS, address=leaf_address)),
        if_false=descend,
    )
    entry_address = pre.deploy_contract(code=frame_code)

    # gas_cost counts both Conditional branches and a cold leaf CALL,
    # so the estimate is conservative and the clamp errs shallow.
    mem_expansion = fork.memory_expansion_gas_calculator()
    frame_gas = frame_code.gas_cost(fork) + mem_expansion(new_bytes=mem_size)

    def reachable_depth(execution_gas: int) -> int:
        """Return the deepest frame the budget can fund."""
        frames = 0
        while True:
            forwarded_gas = execution_gas - frame_gas
            forwarded_gas -= forwarded_gas // 64
            if forwarded_gas < frame_gas:
                return frames
            execution_gas = forwarded_gas
            frames += 1

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32,
        return_cost_deducted_prior_execution=True,
    )

    txs = []
    remaining_gas = gas_benchmark_value
    while remaining_gas > 0:
        execution_gas = min(tx_gas_limit, remaining_gas)
        remaining_gas -= execution_gas
        if execution_gas < intrinsic_gas + frame_gas:
            break
        txs.append(
            Transaction(
                to=entry_address,
                gas_limit=execution_gas,
                data=Hash(
                    min(
                        depth,
                        reachable_depth(execution_gas - intrinsic_gas),
                    )
                ),
                sender=pre.fund_eoa(),
            )
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        skip_gas_used_validation=True,
        expected_receipt_status=1,
    )
