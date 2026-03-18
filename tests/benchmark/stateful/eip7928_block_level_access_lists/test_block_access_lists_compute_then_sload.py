"""
Tests for EIP-7928 BAL with computation followed by SLOADs.

Deploys a contract that reads three parameters from storage: cursor
position (CURSOR_SLOT), SLOAD count (ITEMS_PER_TX_SLOT), and
computation iterations (COMPUTE_ITERS_SLOT).  It first runs a
compute loop, then SLOADs sequential slots starting at cursor,
and finally writes the updated cursor.

The ``compute_percent`` parameter controls the gas split between
the compute and SLOAD phases.
"""

import pytest
from execution_testing import (
    Alloc,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Op,
    Storage,
)

from .helpers import (
    COMPUTE_ITERS_SLOT,
    CURSOR_OVERHEAD_GAS,
    CURSOR_SLOT,
    ITEMS_PER_TX_SLOT,
    build_contract_expectation,
    run_bal_benchmark,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

GAS_PER_COMPUTE_ITERATION = 60
GAS_PER_SLOAD_ITERATION = 2_200

# Extra overhead for the third SLOAD (COMPUTE_ITERS_SLOT).
_EXTRA_OVERHEAD = CURSOR_OVERHEAD_GAS + 2_100


def create_compute_then_sload_contract() -> Bytecode:
    """
    Create contract with compute phase then SLOAD phase via cursor.

    1. cursor         = SLOAD(CURSOR_SLOT)
    2. sload_count    = SLOAD(ITEMS_PER_TX_SLOT)
    3. compute_iters  = SLOAD(COMPUTE_ITERS_SLOT)
    4. Compute loop:  accumulator = accumulator * 3 + 7
    5. SLOAD loop:    SLOAD(cursor + i) for i in 0..sload_count-1
    6. SSTORE(CURSOR_SLOT, cursor + sload_count)
    """
    compute_loop_start = 17
    compute_end = 40
    sload_loop_start = 45
    sload_end = 68

    code = (
        # 1-3. Read cursor, sload_count, compute_iters
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD  # stack: [cursor]
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD  # stack: [sload_count, cursor]
        + Op.PUSH3(COMPUTE_ITERS_SLOT)
        + Op.SLOAD  # stack: [compute_iters, sload_count, cursor]
        # 4. Compute loop: accumulator = 1
        + Op.PUSH1(0x01)  # stack: [acc, iters, sload_count, cursor]
        + Op.JUMPDEST  # compute_loop_start
        + Op.SWAP1
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(compute_end)
        + Op.JUMPI
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH1(0x03)
        + Op.MUL
        + Op.PUSH1(0x07)
        + Op.ADD
        + Op.PUSH2(compute_loop_start)
        + Op.JUMP
        + Op.JUMPDEST  # compute_end
        + Op.POP  # drop iters=0
        + Op.POP  # drop accumulator
        # stack: [sload_count, cursor]
        # 5. SLOAD loop: current = cursor
        + Op.DUP2  # stack: [current, sload_count, cursor]
        + Op.SWAP1  # stack: [sload_count, current, cursor]
        + Op.JUMPDEST  # sload_loop_start
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(sload_end)
        + Op.JUMPI
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
        + Op.PUSH2(sload_loop_start)
        + Op.JUMP
        + Op.JUMPDEST  # sload_end
        # stack: [0, cursor_end, cursor_start]
        + Op.POP
        # 6. Write updated cursor
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE  # SSTORE(CURSOR_SLOT, cursor_end)
        + Op.POP  # drop cursor_start
        + Op.STOP
    )
    return code


def _compute_params(
    fork: Fork,
    compute_percent: int,
) -> tuple[int, int, int, int, int]:
    """Return (num_txs, sload_per_tx, compute_per_tx, total, max_gas)."""
    gas_costs = fork.gas_costs()
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None

    block_gas_limit = int(Environment().gas_limit)
    num_txs = block_gas_limit // max_tx_gas

    available = max_tx_gas - gas_costs.G_TRANSACTION - _EXTRA_OVERHEAD
    compute_gas = int(available * compute_percent / 100)
    sload_gas = available - compute_gas

    compute_per_tx = compute_gas // GAS_PER_COMPUTE_ITERATION
    sload_per_tx = sload_gas // GAS_PER_SLOAD_ITERATION
    total = num_txs * sload_per_tx
    return num_txs, sload_per_tx, compute_per_tx, total, max_tx_gas


@pytest.mark.parametrize(
    "compute_percent",
    [5, 10, 25, 50],
    ids=lambda p: f"compute_{p}pct",
)
def test_bal_compute_then_sload(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    compute_percent: int,
) -> None:
    """Test BAL with computation phase followed by SLOAD phase."""
    num_txs, sload_per_tx, compute_per_tx, total, max_gas = _compute_params(
        fork, compute_percent
    )
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {
            CURSOR_SLOT: 0,
            ITEMS_PER_TX_SLOT: sload_per_tx,
            COMPUTE_ITERS_SLOT: compute_per_tx,
        }
    )
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_compute_then_sload_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=sload_per_tx,
        gas_limit=max_gas,
        contract_expectation=build_contract_expectation(
            num_txs,
            sload_per_tx,
            list(range(total)) + [COMPUTE_ITERS_SLOT],
        ),
    )


@pytest.mark.parametrize(
    "compute_percent",
    [10, 50],
    ids=lambda p: f"compute_{p}pct",
)
def test_bal_compute_then_sload_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    compute_percent: int,
) -> None:
    """Simple validation test with 20 SLOADs across 2 transactions."""
    total_slots = 20
    sload_per_tx = 10
    num_txs = 2

    gas_budget = 400_000
    compute_gas = int(gas_budget * compute_percent / 100)
    compute_iters = compute_gas // GAS_PER_COMPUTE_ITERATION

    storage = Storage(
        {i: i + 1 for i in range(total_slots)}  # type: ignore
        | {
            CURSOR_SLOT: 0,
            ITEMS_PER_TX_SLOT: sload_per_tx,
            COMPUTE_ITERS_SLOT: compute_iters,
        }
    )
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_compute_then_sload_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=sload_per_tx,
        gas_limit=500_000,
        contract_expectation=build_contract_expectation(
            num_txs,
            sload_per_tx,
            list(range(total_slots)) + [COMPUTE_ITERS_SLOT],
        ),
    )
