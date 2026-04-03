"""
Tests for EIP-7928 BAL with dependent pointer-chasing SLOADs.

Deploys a contract with linked-list storage (slot[i] = i+1) that
reads its starting position from CURSOR_SLOT.  Each transaction
follows the chain while remaining gas exceeds a threshold, then
writes the final chased value back to CURSOR_SLOT, creating
inter-transaction dependencies.
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
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _chase_body() -> Bytecode:
    """
    Pointer-chase loop body.

    Stack on entry:  [cursor]
    Stack on exit:   [new_cursor]
    """
    return Op.DUP1 + Op.SLOAD + Op.SWAP1 + Op.POP


def create_pointer_chase_contract(
    gas_threshold: int,
) -> Bytecode:
    """
    Create contract that follows a pointer chain via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. Loop while GAS > threshold: cursor = SLOAD(cursor)
    3. SSTORE(CURSOR_SLOT, cursor)
    """
    return gas_check_loop_contract(
        setup=cursor_read(),
        body=_chase_body(),
        gas_threshold=gas_threshold,
    )


def test_bal_max_pointer_chase(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Test BAL with maximum dependent pointer-chasing SLOADs."""
    body_gas = _chase_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
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
        contract_code=create_pointer_chase_contract(plan.gas_threshold),
        contract_storage=storage,
        plan=plan,
        data_slot_reads=list(range(1, total + 1)),
    )
