"""
Tests for EIP-7928 BAL with cross-contract pointer chasing.

Uses a **dispatcher contract** that all transactions call.  The
dispatcher reads a cursor (chain index) from CURSOR_SLOT, looks up
the chain entry-point address from its own storage, CALLs it, and
increments the cursor.

Each chain is a series of contracts linked through storage slot 0:
contract N stores the address of contract N+1.  The last contract
stores zero (sentinel).

The cursor mechanism ensures TX N+1 depends on TX N's state,
requiring the BAL to parallelize execution.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageSlot,
    BenchmarkTestFiller,
    Block,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    Op,
    Storage,
    TestPhaseManager,
    Transaction,
)
from execution_testing.base_types.base_types import HashInt

from .helpers import (
    CURSOR_INIT,
    CURSOR_SLOT,
    cursor_read,
    cursor_write,
)
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

MAX_CALL_DEPTH = 100


def create_dispatcher_contract() -> Bytecode:
    """
    Create dispatcher: read cursor, look up entry, CALL, bump cursor.

    1. chain_idx   = SLOAD(CURSOR_SLOT)
    2. entry_addr  = SLOAD(chain_idx)
    3. CALL(entry_addr)
    4. SSTORE(CURSOR_SLOT, chain_idx + 1)
    """
    return (
        cursor_read()
        + Op.DUP1
        + Op.SLOAD
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.DUP6
        + Op.GAS
        + Op.CALL
        + Op.POP
        + Op.POP
        + Op.PUSH1(0x01)
        + Op.ADD
        + cursor_write()
        + Op.STOP
    )


def create_chain_contract() -> Bytecode:
    """
    Create contract that reads slot 0 and CALLs that address.

    Reads next_addr from slot 0; if zero (sentinel) skips the CALL.
    """
    check = Op.PUSH1(0x00) + Op.SLOAD + Op.DUP1 + Op.ISZERO
    call_body = (
        Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.DUP6
        + Op.GAS
        + Op.CALL
        + Op.POP
    )
    end = len(check) + 2 + 1 + len(call_body)  # +PUSH1+JUMPI
    return check + Op.PUSH1(end) + Op.JUMPI + call_body + Op.JUMPDEST + Op.STOP


def _compute_tx_gas_limits(
    block_gas_limit: int,
    max_tx_gas: int,
    intrinsic_gas: int,
) -> list[int]:
    """
    Fill block with txs, last tx gets remaining gas.

    Skip the last tx if remaining gas cannot cover intrinsic cost.
    """
    gas_limits: list[int] = []
    remaining = block_gas_limit
    while remaining >= intrinsic_gas:
        g = min(remaining, max_tx_gas)
        if g < intrinsic_gas:
            break
        gas_limits.append(g)
        remaining -= g
    return gas_limits


def _max_chain_depth(
    fork: Fork,
    gas_for_chain: int,
) -> int:
    """
    Simulate nested CALL gas forwarding (63/64 rule).

    Each chain contract SLOADs slot 0, then CALLs the next
    contract.  The 63/64 rule (EIP-150) means each depth
    receives exponentially less gas.  Return the max depth
    where every contract has enough gas to execute.
    """
    # Chain contract before CALL: SLOAD(0) + check + push args.
    # Mirrors create_chain_contract non-sentinel path up to CALL.
    check = Op.PUSH1(0x00) + Op.SLOAD + Op.DUP1 + Op.ISZERO
    skip_jump = Op.PUSH1(0x00) + Op.JUMPI
    call_args = (
        Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.DUP6
        + Op.GAS
    )
    pre_call = (check + skip_jump + call_args).gas_cost(fork)
    call_base = Op.CALL.gas_cost(fork)

    # Sentinel (last contract): SLOAD(0) returns 0, JUMPI taken.
    sentinel_cost = (
        check + Op.PUSH1(0x00) + Op.JUMPI + Op.JUMPDEST + Op.STOP
    ).gas_cost(fork)

    gas = gas_for_chain
    depth = 0
    while depth < MAX_CALL_DEPTH:
        if gas < sentinel_cost:
            break
        after_call_base = gas - pre_call - call_base
        if after_call_base <= 0:
            # Enough for sentinel but not another hop.
            depth += 1
            break
        forwarded = after_call_base * 63 // 64
        if forwarded < sentinel_cost:
            depth += 1
            break
        gas = forwarded
        depth += 1
    return depth


def _calculate_params(
    fork: Fork,
    gas_limits: list[int],
) -> tuple[int, int]:
    """Return (num_transactions, chain_length)."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Dispatcher gas consumed before its CALL forwards gas.
    dispatcher_pre_call = (
        cursor_read()
        + Op.DUP1
        + Op.SLOAD
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Op.DUP6
        + Op.GAS
    ).gas_cost(fork)
    dispatcher_call_base = Op.CALL.gas_cost(fork)

    min_gas = min(gas_limits)
    after_dispatcher = (
        min_gas - intrinsic_gas - dispatcher_pre_call - dispatcher_call_base
    )
    # 63/64 forwarded from dispatcher's CALL to chain[0].
    gas_for_chain = after_dispatcher * 63 // 64
    chain_length = _max_chain_depth(fork, gas_for_chain)
    return len(gas_limits), chain_length


def _run_cross_contract_chase(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    gas_limits: list[int],
    chain_length: int,
) -> None:
    """Run a cross-contract chase benchmark."""
    chain_code = create_chain_contract()
    num_transactions = len(gas_limits)
    total_contracts = num_transactions * chain_length

    # Deploy all chain contracts.
    contracts: list[Address] = []
    for _ in range(total_contracts):
        c = pre.deploy_contract(code=chain_code, storage=Storage({}))
        contracts.append(c)

    # Link contracts within each chain.
    for tx_idx in range(num_transactions):
        start = tx_idx * chain_length
        for i in range(chain_length - 1):
            current = contracts[start + i]
            next_addr = contracts[start + i + 1]
            account = pre[current]
            assert account is not None
            account.storage[0] = int.from_bytes(Address(next_addr), "big")

    # Deploy dispatcher with entry-point lookup table.
    # Chain entries at slots CURSOR_INIT..CURSOR_INIT+N-1;
    # cursor at slot 0 starts at CURSOR_INIT.
    entry_storage: dict[HashInt, HashInt] = {
        HashInt(CURSOR_INIT + tx_idx): HashInt(
            int.from_bytes(Address(contracts[tx_idx * chain_length]), "big")
        )
        for tx_idx in range(num_transactions)
    }
    entry_storage[HashInt(CURSOR_SLOT)] = HashInt(CURSOR_INIT)
    dispatcher = pre.deploy_contract(
        code=create_dispatcher_contract(),
        storage=Storage(entry_storage),
    )

    # All TXs call the dispatcher with empty calldata.
    # Single sender prevents trivial per-sender optimizations.
    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        transactions = [
            Transaction(
                sender=sender,
                to=dispatcher,
                gas_limit=gas_limits[i],
                data=b"",
            )
            for i in range(num_transactions)
        ]

    # BAL expectations.
    account_expectations: dict[Address, BalAccountExpectation] = {}

    account_expectations[dispatcher] = BalAccountExpectation(
        storage_reads=list(range(CURSOR_INIT, CURSOR_INIT + num_transactions)),
        storage_changes=[
            BalStorageSlot(
                slot=CURSOR_SLOT,
                validate_any_change=True,
            ),
        ],
    )

    account_expectations[sender] = BalAccountExpectation(
        nonce_changes=[
            BalNonceChange(
                block_access_index=tx_idx + 1,
                post_nonce=tx_idx + 1,
            )
            for tx_idx in range(num_transactions)
        ],
    )

    for contract in contracts:
        account_expectations[contract] = BalAccountExpectation(
            storage_reads=[0]
        )

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post: dict[Address, Account] = {
        sender: Account(nonce=num_transactions),
    }

    benchmark_test(
        pre=pre, post=post, blocks=[block], skip_gas_used_validation=True
    )


def test_bal_cross_contract_chase(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Test BAL with cross-contract pointer chasing."""
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None
    intrinsic = fork.transaction_intrinsic_cost_calculator()()

    gas_limits = _compute_tx_gas_limits(
        gas_benchmark_value, max_tx_gas, intrinsic
    )
    _, chain_length = _calculate_params(fork, gas_limits)
    _run_cross_contract_chase(pre, benchmark_test, gas_limits, chain_length)
