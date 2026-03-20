"""
Tests for EIP-7928 BAL with mixed computation and SLOADs.

Each loop iteration performs N compute steps (pure arithmetic)
followed by one SLOAD + cursor increment.  The ``compute_percent``
parameter controls N so that approximately that fraction of each
iteration's gas is spent on computation vs. storage reads.
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


def _compute_step() -> Bytecode:
    """
    One pure-compute step (stack unchanged).

    Uses cursor on stack: DUP, multiply by 3, add 7, discard.
    """
    return Op.DUP1 + Op.PUSH1(0x03) + Op.MUL + Op.PUSH1(0x07) + Op.ADD + Op.POP


def _compute_steps_for_percent(
    fork: Fork,
    compute_percent: int,
) -> int:
    """Return N compute steps per SLOAD for a target gas ratio."""
    sload_gas = sload_loop_body().gas_cost(fork)
    step_gas = _compute_step().gas_cost(fork)
    # N = pct * sload_gas / (step_gas * (100 - pct))
    n = compute_percent * sload_gas / (step_gas * (100 - compute_percent))
    return max(1, round(n))


def _mixed_body(compute_steps: int) -> Bytecode:
    """N compute steps then SLOAD(cursor) + cursor++."""
    step = _compute_step()
    body = step
    for _ in range(compute_steps - 1):
        body += step
    return body + sload_loop_body()


@pytest.mark.parametrize(
    "compute_percent",
    [5, 10, 25, 50],
    ids=lambda p: f"compute_{p}pct",
)
def test_bal_compute_then_sload(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    compute_percent: int,
) -> None:
    """Test BAL with mixed computation and SLOAD per iteration."""
    n = _compute_steps_for_percent(fork, compute_percent)
    body = _mixed_body(n)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body.gas_cost(fork),
        setup_gas=cursor_read().gas_cost(fork),
        gas_benchmark_value=gas_benchmark_value,
    )
    total = plan.total_iterations
    storage = Storage(
        {i: i + 1 for i in range(total + 1)}  # type: ignore
    )
    run_bal_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        contract_code=gas_check_loop_contract(
            setup=cursor_read(),
            body=body,
            gas_threshold=plan.gas_threshold,
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=list(range(1, total + 1)),
    )
