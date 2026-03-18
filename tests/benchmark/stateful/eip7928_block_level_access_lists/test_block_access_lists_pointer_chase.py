"""
Tests for EIP-7928 BAL with dependent pointer-chasing SLOADs.

Deploys a contract with linked-list storage (slot[i] = i+1) that reads
its starting position from CURSOR_SLOT.  Each transaction follows the
chain for ITEMS_PER_TX_SLOT steps, then writes the final chased value
back to CURSOR_SLOT, creating inter-transaction dependencies.
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


def _chase_loop_iteration() -> Bytecode:
    """Return bytecode for one pointer-chase loop iteration."""
    return (
        Op.JUMPDEST
        + Op.DUP2
        + Op.ISZERO
        + Op.PUSH2(0)
        + Op.JUMPI
        + Op.DUP1
        + Op.SLOAD
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH2(0)
        + Op.JUMP
    )


def create_pointer_chase_contract() -> Bytecode:
    """
    Create contract that follows a pointer chain via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. count  = SLOAD(ITEMS_PER_TX_SLOT)
    3. Loop count times: cursor = SLOAD(cursor)
    4. SSTORE(CURSOR_SLOT, cursor)   (chased value IS the new cursor)
    """
    loop_start = 11
    loop_end = 32
    code = (
        # 1. Read cursor and count
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD  # stack: [cursor]
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD  # stack: [count, cursor]
        + Op.SWAP1  # stack: [cursor, count]
        # Loop: while count > 0
        + Op.JUMPDEST  # loop_start
        + Op.DUP2
        + Op.ISZERO
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        # cursor = SLOAD(cursor)
        + Op.DUP1
        + Op.SLOAD
        + Op.SWAP1
        + Op.POP  # replace old cursor with new
        # count -= 1
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH2(loop_start)
        + Op.JUMP
        + Op.JUMPDEST  # loop_end
        # stack: [cursor_final, 0]
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE  # SSTORE(CURSOR_SLOT, cursor_final)
        + Op.POP  # drop count=0
        + Op.STOP
    )
    return code


def test_bal_max_pointer_chase(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum dependent pointer-chasing SLOADs."""
    gas_per_iteration = _chase_loop_iteration().gas_cost(fork)
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
        contract_code=create_pointer_chase_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=max_gas,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, list(range(total))
        ),
    )


def test_bal_pointer_chase_simple(
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
        contract_code=create_pointer_chase_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=500_000,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, list(range(total_slots))
        ),
    )
