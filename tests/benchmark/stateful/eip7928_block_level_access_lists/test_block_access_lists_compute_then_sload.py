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
    gas_check_loop_contract,
    plan_benchmark,
    run_bal_benchmark,
    sload_loop_body,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _compute_loop(
    loop_start: int = 0,
    loop_end: int = 0,
) -> Bytecode:
    """
    Return the fixed-count compute loop (accumulator * 3 + 7).

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
    # Read cursor, compute_iters, init accumulator.
    # stack after: [acc=1, iters, cursor]
    setup = (
        cursor_read()
        + Op.PUSH3(COMPUTE_ITERS_SLOT)
        + Op.SLOAD
        + Op.PUSH1(0x01)
    )

    # Compute loop with resolved jump targets.
    compute_start = len(setup)
    compute_end = compute_start + len(_compute_loop())
    compute = _compute_loop(compute_start, compute_end)

    # Drop compute results → stack: [cursor]
    transition = Op.JUMPDEST + Op.POP + Op.POP

    # Gas-check SLOAD loop built by helper.
    return gas_check_loop_contract(
        setup=setup + compute + transition,
        body=sload_loop_body(),
        gas_threshold=gas_threshold,
    )


def _setup_gas(fork: Fork, compute_iters: int) -> int:
    """Gas for setup + fixed compute phase before the SLOAD loop."""
    base = (
        cursor_read()
        + Op.PUSH3(COMPUTE_ITERS_SLOT)
        + Op.SLOAD
    )
    transition = Op.JUMPDEST + Op.POP + Op.POP
    return (
        base.gas_cost(fork)
        + Op.PUSH1(0x01).gas_cost(fork)
        + compute_iters * _compute_loop().gas_cost(fork)
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
    return compute_gas // _compute_loop().gas_cost(fork)


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
        contract_code=create_compute_then_sload_contract(
            plan.gas_threshold
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=(
            list(range(total)) + [COMPUTE_ITERS_SLOT]
        ),
    )
