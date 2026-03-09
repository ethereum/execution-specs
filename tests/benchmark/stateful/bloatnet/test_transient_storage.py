"""
abstract: Transient storage benchmark cases for TSTORE/TLOAD saturation.

   These tests stress transient storage (EIP-1153) by performing
   massive numbers of TSTORE/TLOAD operations within a single block.
   Unlike persistent SSTORE (20K gas), TSTORE costs only 100 gas with
   no cold/warm distinction, enabling vastly more writes per block.
"""

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

from tests.benchmark.stateful.helpers import (
    DECREMENT_COUNTER_CONDITION,
    build_benchmark_txs,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# TSTORE SATURATION BENCHMARK ARCHITECTURE:
#
#   test_tstore_unique_keys:
#   Simple loop contract that TSTOREs at incrementing keys.
#   At 100 gas per TSTORE + ~56 gas loop overhead, each iteration
#   costs ~156 gas, yielding ~64K iterations per 10M gas benchmark.
#   Creates massive in-memory trie pressure without persistent state
#   overhead — fundamentally different stress than SSTORE.
#
#   test_tstore_same_key:
#   Repeatedly TSTOREs the same key (slot 0). Uses JumpLoopGenerator
#   (max code fill) for maximum throughput. Tests the transient
#   storage hot-path optimization in clients.
#
# WHY IT STRESSES CLIENTS:
#   - TSTORE at 100 gas enables ~300K ops per 30M gas block
#   - Each unique key expands the in-memory transient trie
#   - Transient storage is cleared per-transaction, so clients
#     must allocate and deallocate rapidly
#   - No persistent state: tests pure in-memory data structure
#     performance without disk I/O


@pytest.mark.parametrize("with_tload", [True, False])
def test_tstore_unique_keys(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    with_tload: bool,
) -> None:
    """
    Benchmark TSTORE with unique keys per iteration.

    Saturate transient storage by writing incrementing keys.
    Optionally follow each TSTORE with a TLOAD readback to stress
    both write and read paths.
    """
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
    """
    Benchmark TSTORE writing the same key repeatedly.

    Measure transient storage hot-path performance by repeatedly
    writing to slot 0. Uses JumpLoopGenerator for maximum code fill.
    """
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
