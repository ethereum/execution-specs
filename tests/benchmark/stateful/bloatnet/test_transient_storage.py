"""Benchmark transient storage operations (TSTORE/TLOAD)."""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    JumpLoopGenerator,
    Op,
    While,
)

from tests.benchmark.helper.loops import DECREMENT_COUNTER_CONDITION
from tests.benchmark.helper.transactions import build_benchmark_txs


@pytest.mark.parametrize("with_tload", [True, False])
def test_tstore_unique_keys(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    with_tload: bool,
) -> None:
    """Benchmark TSTORE with a unique key per iteration."""
    # Memory layout: MEM[0..31] = counter (incrementing)
    setup = (
        Op.MSTORE(
            0,
            Op.CALLDATALOAD(32),  # starting counter
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.CALLDATALOAD(0)  # [num_iters]
    )

    # TSTORE(counter, 1) — write to unique transient key
    body = Op.TSTORE(Op.MLOAD(0), 1)

    if with_tload:
        # TLOAD readback — stress write+read pattern
        body += Op.POP(Op.TLOAD(Op.MLOAD(0)))

    # Increment counter in memory
    body += Op.MSTORE(0, Op.ADD(Op.MLOAD(0), 1))

    loop = While(
        body=body,
        condition=DECREMENT_COUNTER_CONDITION,
    )

    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    txs, total_gas_consumed = build_benchmark_txs(
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        attack_contract_address=attack_contract_address,
        setup_cost=setup.gas_cost(fork),
        iteration_cost=loop.gas_cost(fork),
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_consumed,
    )


@pytest.mark.parametrize("with_tload", [True, False])
def test_tstore_same_key(
    benchmark_test: BenchmarkTestFiller,
    with_tload: bool,
) -> None:
    """Benchmark TSTORE writing the same key repeatedly."""
    attack_block = Op.TSTORE(0, 1)

    if with_tload:
        attack_block += Op.POP(Op.TLOAD(0))

    benchmark_test(
        target_opcode=Op.TSTORE,
        code_generator=JumpLoopGenerator(
            setup=Bytecode(),
            attack_block=attack_block,
        ),
    )
