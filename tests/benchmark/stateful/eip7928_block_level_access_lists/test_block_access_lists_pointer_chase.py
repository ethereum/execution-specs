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
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _chase_loop_iteration(
    loop_start: int = 0,
    loop_end: int = 0,
) -> Bytecode:
    """
    Return bytecode for one pointer-chase loop iteration.

    Pass loop_start/loop_end for contract assembly; omit them
    (defaults to 0) when calling ``.gas_cost(fork)``.
    """
    return (
        Op.JUMPDEST
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
    )


def create_pointer_chase_contract() -> Bytecode:
    """
    Create contract that follows a pointer chain via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. count  = SLOAD(ITEMS_PER_TX_SLOT)
    3. Loop count times: cursor = SLOAD(cursor)
    4. SSTORE(CURSOR_SLOT, cursor)   (chased value IS the new cursor)
    """
    setup = cursor_read() + Op.SWAP1  # stack: [cursor, count]
    loop_start = len(setup)
    loop_end = loop_start + len(_chase_loop_iteration())
    loop = _chase_loop_iteration(loop_start, loop_end)
    teardown = (
        Op.JUMPDEST  # loop_end
        # stack: [cursor_final, 0]
        + cursor_write()  # SSTORE(CURSOR_SLOT, cursor_final)
        + Op.POP  # drop count=0
        + Op.STOP
    )
    return setup + loop + teardown


def test_bal_max_pointer_chase(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum dependent pointer-chasing SLOADs."""
    gas_costs = fork.gas_costs()
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None
    block_gas_limit = int(Environment().gas_limit)
    num_txs = block_gas_limit // max_tx_gas

    overhead = cursor_overhead_gas(fork)
    available = max_tx_gas - gas_costs.G_TRANSACTION - overhead
    gas_per_iteration = _chase_loop_iteration().gas_cost(fork)
    items_per_tx = available // gas_per_iteration
    total = num_txs * items_per_tx

    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx}
    )
    run_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        contract_code=create_pointer_chase_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=max_tx_gas,
    )


def test_bal_pointer_chase_simple(
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
        contract_code=create_pointer_chase_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=500_000,
    )
