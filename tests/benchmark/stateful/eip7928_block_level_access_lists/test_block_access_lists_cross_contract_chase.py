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
    BalStorageChange,
    BalStorageSlot,
    BenchmarkTestFiller,
    Block,
    BlockAccessListExpectation,
    Bytecode,
    Environment,
    Fork,
    Op,
    Storage,
    TestPhaseManager,
    Transaction,
)

from .helpers import CURSOR_SLOT
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
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD
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
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE
        + Op.STOP
    )


def create_chain_contract() -> Bytecode:
    """
    Create contract that reads slot 0 and CALLs that address.

    Reads next_addr from slot 0; if zero (sentinel) skips the CALL.
    """
    check = (
        Op.PUSH1(0x00) + Op.SLOAD + Op.DUP1 + Op.ISZERO
    )
    call_body = (
        Op.PUSH1(0x00) + Op.PUSH1(0x00) + Op.PUSH1(0x00)
        + Op.PUSH1(0x00) + Op.PUSH1(0x00)
        + Op.DUP6 + Op.GAS + Op.CALL + Op.POP
    )
    end = len(check) + 2 + 1 + len(call_body)  # +PUSH1+JUMPI
    return (
        check
        + Op.PUSH1(end)
        + Op.JUMPI
        + call_body
        + Op.JUMPDEST
        + Op.STOP
    )


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


def _calculate_params(
    fork: Fork,
    gas_limits: list[int],
) -> tuple[int, int]:
    """Return (num_transactions, chain_length)."""
    gas_costs = fork.gas_costs()
    dispatcher_cost = create_dispatcher_contract().gas_cost(fork)
    chain_hop_cost = create_chain_contract().gas_cost(fork)
    # Use the smallest tx gas to determine chain length.
    min_gas = min(gas_limits)
    available = (
        min_gas - gas_costs.G_TRANSACTION - dispatcher_cost
    )
    chain_by_gas = available // chain_hop_cost
    chain_length = min(chain_by_gas, MAX_CALL_DEPTH)
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
        c = pre.deploy_contract(
            code=chain_code, storage=Storage({})
        )
        contracts.append(c)

    # Link contracts within each chain.
    for tx_idx in range(num_transactions):
        start = tx_idx * chain_length
        for i in range(chain_length - 1):
            current = contracts[start + i]
            next_addr = contracts[start + i + 1]
            pre[current].storage[0] = int.from_bytes(
                Address(next_addr), "big"
            )

    # Deploy dispatcher with entry-point lookup table.
    entry_storage: dict[int, int] = {
        tx_idx: int.from_bytes(
            Address(contracts[tx_idx * chain_length]), "big"
        )
        for tx_idx in range(num_transactions)
    }
    entry_storage[CURSOR_SLOT] = 0
    dispatcher = pre.deploy_contract(
        code=create_dispatcher_contract(),
        storage=Storage(entry_storage),
    )

    # All TXs call the dispatcher with empty calldata.
    with TestPhaseManager.execution():
        senders = [
            pre.fund_eoa() for _ in range(num_transactions)
        ]
        transactions = [
            Transaction(
                sender=senders[i],
                to=dispatcher,
                gas_limit=gas_limits[i],
                data=b"",
            )
            for i in range(num_transactions)
        ]

    # BAL expectations.
    account_expectations: dict[
        Address, BalAccountExpectation
    ] = {}

    account_expectations[dispatcher] = BalAccountExpectation(
        storage_reads=sorted(range(num_transactions)),
        storage_changes=[
            BalStorageSlot(
                slot=CURSOR_SLOT,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=tx_idx + 1,
                        post_value=tx_idx + 1,
                    )
                    for tx_idx in range(num_transactions)
                ],
            ),
        ],
    )

    for tx_idx, sender in enumerate(senders):
        account_expectations[sender] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=tx_idx + 1,
                    post_nonce=1,
                )
            ],
        )

    for contract in contracts:
        account_expectations[contract] = (
            BalAccountExpectation(storage_reads=[0])
        )

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post: dict[Address, Account] = {}
    for sender in senders:
        post[sender] = Account(nonce=1)

    benchmark_test(pre=pre, post=post, blocks=[block])


def test_bal_cross_contract_chase(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Test BAL with cross-contract pointer chasing."""
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None
    block_gas_limit = int(Environment().gas_limit)
    intrinsic = fork.gas_costs().G_TRANSACTION

    gas_limits = _compute_tx_gas_limits(
        block_gas_limit, max_tx_gas, intrinsic
    )
    _, chain_length = _calculate_params(fork, gas_limits)
    _run_cross_contract_chase(
        pre, benchmark_test, gas_limits, chain_length
    )


def test_bal_cross_contract_chase_simple(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
) -> None:
    """Simple validation test with 10 contracts across 2 txs."""
    _run_cross_contract_chase(
        pre,
        benchmark_test,
        gas_limits=[500_000, 500_000],
        chain_length=5,
    )
