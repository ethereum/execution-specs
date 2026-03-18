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
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
)

from .helpers import (
    CURSOR_SLOT,
    ITEMS_PER_TX_SLOT,
    build_contract_expectation,
    calculate_benchmark_params,
    cursor_read,
    cursor_write,
    run_bal_benchmark,
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
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum sequential SLOADs via cursor."""
    gas_per_iteration = sload_loop_iteration().gas_cost(fork)
    num_txs, items_per_tx, total, max_gas = calculate_benchmark_params(
        fork, gas_per_iteration
    )
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx}
    )
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_sload_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=max_gas,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, list(range(total))
        ),
    )


def test_bal_sloads_loop_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
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
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_sload_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=500_000,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, list(range(total_slots))
        ),
    )
