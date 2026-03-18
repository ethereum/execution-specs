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
    run_bal_benchmark,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _sload_loop_iteration() -> Bytecode:
    """Return bytecode for one SLOAD loop iteration."""
    return (
        Op.JUMPDEST
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(0)
        + Op.JUMPI
        + Op.DUP2
        + Op.SLOAD
        + Op.POP
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(0)
        + Op.JUMP
    )


def create_sload_loop_contract() -> Bytecode:
    """
    Create contract that SLOADs sequential slots via cursor.

    1. cursor  = SLOAD(CURSOR_SLOT)
    2. count   = SLOAD(ITEMS_PER_TX_SLOT)
    3. Loop: SLOAD(cursor + i) for i in 0..count-1
    4. SSTORE(CURSOR_SLOT, cursor + count)
    """
    loop_start = 12
    loop_end = 35
    code = (
        # 1. Read cursor and count
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD  # stack: [cursor]
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD  # stack: [count, cursor]
        # 2. current = cursor (DUP cursor as loop variable)
        + Op.DUP2  # stack: [cursor_copy, count, cursor]
        + Op.SWAP1  # stack: [count, cursor_copy, cursor]
        # Loop: while count > 0
        + Op.JUMPDEST  # loop_start
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        # SLOAD(current)
        + Op.DUP2
        + Op.SLOAD
        + Op.POP
        # current += 1
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.SWAP1
        # count -= 1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(loop_start)
        + Op.JUMP
        + Op.JUMPDEST  # loop_end
        # stack: [0, cursor_end, cursor_start]
        + Op.POP  # drop count=0
        # SSTORE(CURSOR_SLOT, cursor_end)
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE
        + Op.POP  # drop cursor_start
        + Op.STOP
    )
    return code


def test_bal_max_sloads(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum sequential SLOADs via cursor."""
    gas_per_iteration = _sload_loop_iteration().gas_cost(fork)
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
