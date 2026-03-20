"""
Tests for EIP-7928 BAL with computation followed by SLOADs.

Deploys a contract that reads two parameters from storage: cursor
position (CURSOR_SLOT) and computation iterations
(COMPUTE_ITERS_SLOT).  It first runs a fixed compute loop, then
SLOADs sequential slots until remaining gas drops below a
threshold, and finally writes the updated cursor.

The ``compute_percent`` parameter controls the gas split between
the compute and SLOAD phases by varying the compute iteration
count.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
)

from .helpers import (
    COMPUTE_ITERS_SLOT,
    CURSOR_SLOT,
    cursor_read,
    cursor_write,
    plan_benchmark,
    run_bal_benchmark,
    sload_loop_body,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _compute_loop_iteration(
    loop_start: int = 0,
    loop_end: int = 0,
) -> Bytecode:
    """
    Return bytecode for one compute loop iteration.

    Pass loop_start/loop_end for contract assembly; omit them
    (defaults to 0) when calling ``.gas_cost(fork)``.
    """
    return (
        Op.JUMPDEST
        + Op.SWAP1
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH1(0x03)
        + Op.MUL
        + Op.PUSH1(0x07)
        + Op.ADD
        + Op.PUSH2(loop_start)
        + Op.JUMP
    )


def create_compute_then_sload_contract(
    gas_threshold: int,
) -> Bytecode:
    """
    Create contract with compute phase then gas-check SLOAD phase.

    1. cursor        = SLOAD(CURSOR_SLOT)
    2. compute_iters = SLOAD(COMPUTE_ITERS_SLOT)
    3. Compute loop:  accumulator = accumulator * 3 + 7
    4. SLOAD loop (gas-check): SLOAD(cursor + i)
    5. SSTORE(CURSOR_SLOT, cursor)
    """
    # 1-2. Read cursor and compute_iters.
    # stack after: [compute_iters, cursor]
    setup = (
        cursor_read()
        + Op.PUSH3(COMPUTE_ITERS_SLOT)
        + Op.SLOAD
        # Compute loop: accumulator = 1
        + Op.PUSH1(0x01)
        # stack: [acc, iters, cursor]
    )

    # Compute loop (fixed-count, counter-based).
    compute_start = len(setup)
    compute_end = compute_start + len(_compute_loop_iteration())
    compute_loop = _compute_loop_iteration(
        compute_start, compute_end
    )

    # Transition: drop compute results, prepare SLOAD loop.
    transition = (
        Op.JUMPDEST  # compute_end
        + Op.POP     # drop iters=0
        + Op.POP     # drop accumulator
        # stack: [cursor]
    )

    # Gas-check SLOAD loop.
    sload_body = sload_loop_body()
    sload_base = compute_end + len(transition)

    sload_header = (
        Op.JUMPDEST
        + Op.GAS
        + Op.PUSH3(gas_threshold)
        + Op.GT
        + Op.ISZERO
    )
    sload_loop_end = (
        sload_base + len(sload_header)
        + 3 + 1           # PUSH2(loop_end) + JUMPI
        + len(sload_body)
        + 3 + 1           # PUSH2(loop_start) + JUMP
    )
    sload_loop_start = sload_base

    sload_loop = (
        sload_header
        + Op.PUSH2(sload_loop_end)
        + Op.JUMPI
        + sload_body
        + Op.PUSH2(sload_loop_start)
        + Op.JUMP
    )

    teardown = (
        Op.JUMPDEST
        + cursor_write()
        + Op.STOP
    )
    return (
        setup + compute_loop + transition + sload_loop + teardown
    )


def _setup_gas(fork: Fork, compute_iters: int) -> int:
    """
    Gas for setup + fixed compute phase.

    Includes cursor SLOAD, compute_iters SLOAD, accumulator
    init, full compute loop, and transition to SLOAD phase.
    """
    base = (
        cursor_read()
        + Op.PUSH3(COMPUTE_ITERS_SLOT)
        + Op.SLOAD
    )
    acc_init = Op.PUSH1(0x01)
    compute_iter_gas = _compute_loop_iteration().gas_cost(fork)
    transition = Op.JUMPDEST + Op.POP + Op.POP
    return (
        base.gas_cost(fork)
        + acc_init.gas_cost(fork)
        + compute_iters * compute_iter_gas
        + transition.gas_cost(fork)
    )


def _compute_iters_for_percent(
    fork: Fork,
    compute_percent: int,
    tx_gas: int,
) -> int:
    """Return compute iterations for a given gas percentage."""
    intrinsic = fork.gas_costs().G_TRANSACTION
    available = tx_gas - intrinsic
    compute_gas = int(available * compute_percent / 100)
    gas_per_compute = _compute_loop_iteration().gas_cost(fork)
    return compute_gas // gas_per_compute


@pytest.mark.parametrize(
    "compute_percent",
    [5, 10, 25, 50],
    ids=lambda p: f"compute_{p}pct",
)
def test_bal_compute_then_sload(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    compute_percent: int,
) -> None:
    """Test BAL with computation phase followed by SLOAD phase."""
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None
    compute_iters = _compute_iters_for_percent(
        fork, compute_percent, max_tx_gas
    )

    body_gas = sload_loop_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=_setup_gas(fork, compute_iters),
    )
    total = plan.total_iterations
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {
            CURSOR_SLOT: 0,
            COMPUTE_ITERS_SLOT: compute_iters,
        }
    )
    run_bal_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        fork=fork,
        contract_code=create_compute_then_sload_contract(
            plan.gas_threshold
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=(
            list(range(total)) + [COMPUTE_ITERS_SLOT]
        ),
    )


@pytest.mark.parametrize(
    "compute_percent",
    [10, 50],
    ids=lambda p: f"compute_{p}pct",
)
def test_bal_compute_then_sload_simple(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    compute_percent: int,
) -> None:
    """Simple validation test with compute + SLOAD across 2 txs."""
    compute_iters = _compute_iters_for_percent(
        fork, compute_percent, 500_000
    )

    body_gas = sload_loop_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=_setup_gas(fork, compute_iters),
        num_transactions=2,
        tx_gas_limit=500_000,
    )
    total = plan.total_iterations
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {
            CURSOR_SLOT: 0,
            COMPUTE_ITERS_SLOT: compute_iters,
        }
    )
    run_bal_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        fork=fork,
        contract_code=create_compute_then_sload_contract(
            plan.gas_threshold
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=(
            list(range(total)) + [COMPUTE_ITERS_SLOT]
        ),
    )
