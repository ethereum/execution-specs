"""Benchmark mixed operations."""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Environment,
    ExtCallGenerator,
    Fork,
    JumpLoopGenerator,
    Op,
)


@pytest.mark.parametrize(
    "pattern",
    [
        Op.STOP,
        Op.JUMPDEST,
        Op.PUSH1[bytes(Op.JUMPDEST)],
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)],
        Op.PUSH1[bytes(Op.JUMPDEST)] + Op.JUMPDEST,
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)] + Op.JUMPDEST,
    ],
    ids=lambda x: x.hex(),
)
def test_jumpdest_analysis(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pattern: Bytecode,
) -> None:
    """
    Test the jumpdest analysis performance of the initcode.

    This benchmark places a very long initcode in the memory and then invoke
    CREATE instructions with this initcode up to the block gas limit. The
    initcode itself has minimal execution time but forces the EVM to perform
    the full jumpdest analysis on the parametrized byte pattern. The initicode
    is modified by mixing-in the returned create address between CREATE
    invocations to prevent caching.
    """
    initcode_size = fork.max_initcode_size()

    # Expand the initcode pattern to the transaction data so it can be used in
    # CALLDATACOPY in the main contract. TODO: tune the tx_data_len param.
    tx_data_len = 1024
    tx_data = pattern * (tx_data_len // len(pattern))
    tx_data += (tx_data_len - len(tx_data)) * bytes(Op.JUMPDEST)
    assert len(tx_data) == tx_data_len
    assert initcode_size % len(tx_data) == 0

    # Prepare the initcode in memory.
    code_prepare_initcode = sum(
        (
            Op.CALLDATACOPY(
                dest_offset=i * len(tx_data), offset=0, size=Op.CALLDATASIZE
            )
            for i in range(initcode_size // len(tx_data))
        ),
        Bytecode(),
    )

    # At the start of the initcode execution, jump to the last opcode.
    # This forces EVM to do the full jumpdest analysis.
    initcode_prefix = Op.JUMP(initcode_size - 1)
    code_prepare_initcode += Op.MSTORE(
        0, Op.PUSH32[bytes(initcode_prefix).ljust(32, bytes(Op.JUMPDEST))]
    )

    # Make sure the last opcode in the initcode is JUMPDEST.
    code_prepare_initcode += Op.MSTORE(
        initcode_size - 32, Op.PUSH32[bytes(Op.JUMPDEST) * 32]
    )

    attack_block = (
        Op.PUSH1[len(initcode_prefix)]
        + Op.MSTORE
        + Op.CREATE(value=Op.PUSH0, offset=Op.PUSH0, size=Op.MSIZE)
    )

    setup = code_prepare_initcode + Op.PUSH0

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={"data": tx_data},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("mem_size", [0, 32, 256, 1024])
@pytest.mark.parametrize("return_size", [0, 32, 256, 1024])
@pytest.mark.parametrize(
    "opcode", [Op.INVALID, Op.STOP, Op.RETURN, Op.REVERT, Op.SELFDESTRUCT]
)
def test_terminate_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    return_size: int,
    mem_size: int,
    pre: Alloc,
    env: Environment,
) -> None:
    """Benchmark Terminating Operations."""
    fee_recipient = pre.fund_eoa(amount=1)
    env.fee_recipient = fee_recipient

    setup = Op.MSTORE8(mem_size - 1, 1) if mem_size > 0 else Bytecode()

    attack_block = Bytecode()
    if opcode == Op.SELFDESTRUCT:
        attack_block = Op.SELFDESTRUCT(Op.COINBASE)
    elif opcode.popped_stack_items > 0:
        attack_block = opcode(Op.PUSH0, return_size)
    else:
        attack_block = opcode

    benchmark_test(
        code_generator=ExtCallGenerator(
            setup=setup,
            attack_block=attack_block,
        ),
    )
