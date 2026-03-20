"""
Tests for EIP-7928 BAL with maximum SLOAD transactions.

Deploys a loop-based contract that reads its starting cursor from
storage, then SLOADs sequential slots until remaining gas drops
below a threshold.  The updated cursor is written back, creating
inter-transaction dependencies that require the BAL for parallel
execution.
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


def create_sload_loop_contract(gas_threshold: int) -> Bytecode:
    """
    Create contract that SLOADs sequential slots via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. Loop while GAS > threshold:
         SLOAD(cursor); cursor++
    3. SSTORE(CURSOR_SLOT, cursor)
    """
    setup = cursor_read()  # stack: [cursor]

    # Gas-check loop header.
    header = (
        Op.JUMPDEST
        + Op.GAS
        + Op.PUSH3(gas_threshold)
        + Op.GT
        + Op.ISZERO
    )
    # loop_end offset: setup + header + PUSH2 + JUMPI + body + PUSH2 + JUMP
    body = sload_loop_body()
    loop_end = (
        len(setup)
        + len(header)
        + 3  # PUSH2(loop_end)
        + 1  # JUMPI
        + len(body)
        + 3  # PUSH2(loop_start)
        + 1  # JUMP
    )
    loop_start = len(setup)

    loop = (
        header
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        + body
        + Op.PUSH2(loop_start)
        + Op.JUMP
    )

    teardown = (
        Op.JUMPDEST  # loop_end
        + cursor_write()
        + Op.STOP
    )
    return setup + loop + teardown


def _setup_gas(fork: Fork) -> int:
    """Gas for the setup phase (cold SLOAD of CURSOR_SLOT)."""
    return cursor_read().gas_cost(fork)


def test_bal_max_sloads(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum sequential SLOADs via cursor."""
    body_gas = sload_loop_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=_setup_gas(fork),
    )
    total = plan.total_iterations
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {CURSOR_SLOT: 0}
    )
    run_bal_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        fork=fork,
        contract_code=create_sload_loop_contract(
            plan.gas_threshold
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=list(range(total)),
    )


def test_bal_sloads_loop_simple(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Simple validation test with a few SLOADs across 2 txs."""
    body_gas = sload_loop_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=_setup_gas(fork),
        num_transactions=2,
        tx_gas_limit=500_000,
    )
    total = plan.total_iterations
    storage = Storage(
        {i: i + 1 for i in range(total)}  # type: ignore
        | {CURSOR_SLOT: 0}
    )
    run_bal_benchmark(
        pre=pre,
        benchmark_test=benchmark_test,
        fork=fork,
        contract_code=create_sload_loop_contract(
            plan.gas_threshold
        ),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=list(range(total)),
    )
