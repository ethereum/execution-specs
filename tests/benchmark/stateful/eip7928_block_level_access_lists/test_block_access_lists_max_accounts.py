"""
Tests for EIP-7928 BAL with maximum unique account accesses.

Deploys a contract that reads its starting offset from CURSOR_SLOT
and the iteration count from ITEMS_PER_TX_SLOT, then calls BALANCE
on sequential addresses.  Each transaction writes an updated cursor,
creating inter-transaction dependencies that require the BAL.
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    BalAccountExpectation,
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

# Start addresses above precompiles and system contracts.
BASE_ADDR = 0x10000


def _balance_loop_iteration() -> Bytecode:
    """Return bytecode for one BALANCE loop iteration."""
    return (
        Op.JUMPDEST
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(0)
        + Op.JUMPI
        + Op.DUP2
        + Op.BALANCE
        + Op.POP
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(0)
        + Op.JUMP
    )


def create_balance_loop_contract() -> Bytecode:
    """
    Create contract that calls BALANCE on sequential addresses via cursor.

    1. cursor = SLOAD(CURSOR_SLOT)           (address offset)
    2. count  = SLOAD(ITEMS_PER_TX_SLOT)
    3. addr   = BASE_ADDR + cursor
    4. Loop count times: BALANCE(addr); addr += 1
    5. SSTORE(CURSOR_SLOT, cursor + count)
    """
    loop_start = 17
    loop_end = 40
    code = (
        # 1. Read cursor and count
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD  # stack: [cursor]
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD  # stack: [count, cursor]
        # 2. addr = BASE_ADDR + cursor
        + Op.SWAP1  # stack: [cursor, count]
        + Op.PUSH3(BASE_ADDR)
        + Op.ADD  # stack: [addr, count]
        + Op.SWAP1  # stack: [count, addr]
        # Loop: while count > 0
        + Op.JUMPDEST  # loop_start
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        # BALANCE(addr)
        + Op.DUP2
        + Op.BALANCE
        + Op.POP
        # addr += 1
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.SWAP1
        # count -= 1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(loop_start)
        + Op.JUMP
        + Op.JUMPDEST  # loop_end
        # stack: [0, addr_end]
        + Op.POP
        # addr_end - BASE_ADDR = new cursor value
        + Op.PUSH3(BASE_ADDR)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE
        + Op.STOP
    )
    return code


def test_bal_max_account_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with maximum unique account accesses via BALANCE."""
    gas_per_iteration = _balance_loop_iteration().gas_cost(fork)
    num_txs, items_per_tx, total, max_gas = calculate_benchmark_params(
        fork, gas_per_iteration
    )
    storage = Storage({CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx})
    extra = {
        Address(BASE_ADDR + i): BalAccountExpectation.empty()
        for i in range(total)
    }
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_balance_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=max_gas,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, data_slot_reads=[]
        ),
        extra_expectations=extra,
    )


def test_bal_account_access_simple(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """Simple validation test with 20 accounts across 2 transactions."""
    total_accounts = 20
    items_per_tx = 10
    num_txs = 2
    storage = Storage({CURSOR_SLOT: 0, ITEMS_PER_TX_SLOT: items_per_tx})
    extra = {
        Address(BASE_ADDR + i): BalAccountExpectation.empty()
        for i in range(total_accounts)
    }
    run_bal_benchmark(
        pre=pre,
        blockchain_test=blockchain_test,
        contract_code=create_balance_loop_contract(),
        contract_storage=storage,
        num_transactions=num_txs,
        items_per_tx=items_per_tx,
        gas_limit=500_000,
        contract_expectation=build_contract_expectation(
            num_txs, items_per_tx, data_slot_reads=[]
        ),
        extra_expectations=extra,
    )
