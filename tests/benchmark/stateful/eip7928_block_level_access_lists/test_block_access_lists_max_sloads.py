"""
Tests for EIP-7928 BAL with maximum SLOAD transactions.

Deploys a loop-based contract that reads its work range from storage
(cursor mechanism) rather than calldata, creating inter-transaction
dependencies that require the BAL for parallel execution.

Each transaction reads CURSOR_SLOT and ITEMS_PER_TX_SLOT, SLOADs
sequential storage slots starting at the cursor, then writes the
updated cursor back.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Environment,
    Fork,
    Op,
    Storage,
)

from .helpers import (
    CURSOR_SLOT,
    ITEMS_PER_TX_SLOT,
    cursor_overhead_gas,
    cursor_read,
    cursor_write,
    run_benchmark,
    sload_loop_iteration,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def create_sload_loop_contract() -> Bytecode:
    """
    Create contract that SLOADs sequential slots via cursor.

    1. cursor  = SLOAD(CURSOR_SLOT)
    2. count   = SLOAD(ITEMS_PER_TX_SLOT)
    3. Loop: SLOAD(cursor + i) for i in 0..count-1
    4. SSTORE(CURSOR_SLOT, cursor + count)
    """
    # stack after setup: [count, cursor_copy, cursor]
    setup = cursor_read() + Op.DUP2 + Op.SWAP1
    loop_start = len(setup)
    loop_end = loop_start + len(sload_loop_iteration())
    loop = sload_loop_iteration(loop_start, loop_end)
    teardown = (
        Op.JUMPDEST  # loop_end
        # stack: [0, cursor_end, cursor_start]
        + Op.POP  # drop count=0
        + cursor_write()  # SSTORE(CURSOR_SLOT, cursor_end)
        + Op.POP  # drop cursor_start
        + Op.STOP
    )
    return setup + loop + teardown


def test_bal_max_sloads(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum sequential SLOADs via cursor."""
    gas_costs = fork.gas_costs()
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None
    block_gas_limit = int(Environment().gas_limit)
    num_txs = block_gas_limit // max_tx_gas

    overhead = cursor_overhead_gas(fork)
    available = max_tx_gas - gas_costs.G_TRANSACTION - overhead
    gas_per_iteration = sload_loop_iteration().gas_cost(fork)
    items_per_tx = available // gas_per_iteration
    total = num_txs * items_per_tx

    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx}
    )
    run_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        contract_code=create_sload_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=max_tx_gas,
    )


def test_bal_sloads_loop_simple(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Simple validation test with 20 slots across 2 transactions."""
    total_slots = 20
    items_per_tx = 10
    num_txs = 2
    storage = Storage(
        {i: i + 1 for i in range(total_slots)}  # type: ignore
        | {CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx}
    )
    run_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        contract_code=create_sload_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=500_000,
    )
