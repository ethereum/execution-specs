"""
Tests for EIP-7928 BAL with maximum unique account accesses.

Deploys a contract that reads its starting offset from CURSOR_SLOT,
then calls BALANCE on sequential addresses while remaining gas
exceeds a threshold.  Each transaction writes an updated cursor,
creating inter-transaction dependencies that require the BAL.
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    BalAccountExpectation,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    Op,
)

from .helpers import (
    CURSOR_INIT,
    StorageInitRange,
    cursor_read,
    cursor_write,
    gas_check_loop_contract,
    plan_benchmark,
    run_bal_benchmark,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

# Start addresses above precompiles and system contracts.
BASE_ADDR = 0x10000


def _balance_body() -> Bytecode:
    """
    BALANCE loop body.

    Stack on entry:  [addr]
    Stack on exit:   [addr+1]
    """
    return Op.DUP1 + Op.BALANCE + Op.POP + Op.PUSH1(0x01) + Op.ADD


def _teardown() -> Bytecode:
    """Teardown: convert addr back to cursor, write, stop."""
    return (
        Op.JUMPDEST
        + Op.PUSH3(BASE_ADDR)
        + Op.SWAP1
        + Op.SUB
        + cursor_write()
        + Op.STOP
    )


def create_balance_loop_contract(
    gas_threshold: int,
) -> Bytecode:
    """
    Create contract that calls BALANCE on sequential addresses.

    1. cursor = SLOAD(CURSOR_SLOT)
    2. addr   = BASE_ADDR + cursor
    3. Loop while GAS > threshold: BALANCE(addr); addr++
    4. SSTORE(CURSOR_SLOT, addr - BASE_ADDR)
    """
    setup = cursor_read() + Op.PUSH3(BASE_ADDR) + Op.ADD
    return gas_check_loop_contract(
        setup=setup,
        body=_balance_body(),
        gas_threshold=gas_threshold,
        teardown=_teardown(),
    )


def test_bal_max_account_access(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """Test BAL with maximum unique account accesses via BALANCE."""
    setup = cursor_read() + Op.PUSH3(BASE_ADDR) + Op.ADD
    body_gas = _balance_body().gas_cost(fork)
    plan = plan_benchmark(
        fork,
        loop_body_gas=body_gas,
        setup_gas=setup.gas_cost(fork),
        gas_benchmark_value=gas_benchmark_value,
        teardown=_teardown(),
    )
    total = plan.total_iterations
    extra = {
        Address(BASE_ADDR + i): BalAccountExpectation.empty()
        for i in range(CURSOR_INIT, total + CURSOR_INIT)
    }
    authority = pre.fund_eoa(amount=0)
    run_bal_benchmark(
        pre=pre,
        fork=fork,
        benchmark_test=benchmark_test,
        contract_code=create_balance_loop_contract(plan.gas_threshold),
        plan=plan,
        tx_gas_limit=tx_gas_limit,
        authority=authority,
        storage_init_ranges=[StorageInitRange(0, 1, CURSOR_INIT)],
        extra_expectations=extra,
    )
