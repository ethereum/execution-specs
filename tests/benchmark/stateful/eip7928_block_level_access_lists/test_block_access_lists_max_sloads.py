"""
Tests for EIP-7928 BAL with maximum SLOAD transactions.

Deploys a loop-based contract that reads its starting cursor from
storage, then SLOADs sequential slots until remaining gas drops
below a threshold.  The updated cursor is written back, creating
inter-transaction dependencies that require the BAL for parallel
execution.

Parametrized over direction: forward (ascending slots) and reverse
(descending slots) to prevent direction-specific optimizations.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
)

from .helpers import (
    StorageInitRange,
    cursor_read,
    gas_check_loop_contract,
    plan_benchmark,
    run_bal_benchmark,
    sload_loop_body,
    sload_loop_body_reverse,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def create_sload_loop_contract(
    gas_threshold: int,
    reverse: bool = False,
) -> Bytecode:
    """
    Create contract that SLOADs sequential slots via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. Loop while GAS > threshold:
         SLOAD(cursor); cursor += 1 (forward) or -= 1 (reverse)
    3. SSTORE(CURSOR_SLOT, cursor)
    """
    body = sload_loop_body_reverse() if reverse else sload_loop_body()
    return gas_check_loop_contract(
        setup=cursor_read(),
        body=body,
        gas_threshold=gas_threshold,
    )


@pytest.mark.parametrize(
    "reverse",
    [False, True],
    ids=["forward", "reverse"],
)
def test_bal_max_sloads(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    reverse: bool,
) -> None:
    """Test BAL with maximum sequential SLOADs via cursor."""
    body = sload_loop_body_reverse() if reverse else sload_loop_body()
    body_gas = body.gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=cursor_read().gas_cost(fork),
        gas_benchmark_value=gas_benchmark_value,
    )
    total = plan.total_iterations
    # Cursor starts at slot 0; forward reads slots 1..total,
    # reverse reads slots total..1.
    cursor_start = total if reverse else 1
    authority = pre.fund_eoa(amount=0)
    run_bal_benchmark(
        pre=pre,
        fork=fork,
        benchmark_test=benchmark_test,
        contract_code=create_sload_loop_contract(
            plan.gas_threshold, reverse=reverse
        ),
        plan=plan,
        tx_gas_limit=tx_gas_limit,
        authority=authority,
        storage_init_ranges=[
            StorageInitRange(1, total, 0),
            StorageInitRange(0, 1, cursor_start),
        ],
        data_slot_reads=list(range(1, total + 1)),
    )
