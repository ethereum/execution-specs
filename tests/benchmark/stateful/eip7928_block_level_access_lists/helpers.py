"""
Shared constants and helpers for BAL benchmark tests.

All cursor-based BAL benchmarks follow the same pattern:
1. Contract reads a cursor from CURSOR_SLOT to know where to start.
2. Contract reads the work-unit count from ITEMS_PER_TX_SLOT.
3. Contract performs test-specific work.
4. Contract writes the updated cursor back to CURSOR_SLOT.

Every transaction sends empty calldata; work parameters live entirely
in storage.  TX N writes CURSOR_SLOT, TX N+1 reads it, creating a
genuine inter-transaction dependency that requires the BAL for
parallel execution.
"""

from __future__ import annotations

from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Op,
    Storage,
    Transaction,
)

# Dedicated storage slots for the cursor mechanism.
# PUSH3-sized values, safely above max data slots (~300 000).
CURSOR_SLOT = 0x100000
ITEMS_PER_TX_SLOT = 0x100001
COMPUTE_ITERS_SLOT = 0x100002


def cursor_overhead_gas(fork: Fork) -> int:
    """
    Return gas overhead per TX for cursor reads + write.

    Two cold SLOADs (CURSOR_SLOT, ITEMS_PER_TX_SLOT) + one cold SSTORE
    (CURSOR_SLOT writeback) + associated PUSH/POP/STOP.
    """
    cursor_ops = (
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD
        + Op.PUSH3(CURSOR_SLOT)
        + Op.SSTORE
        + Op.POP
        + Op.STOP
    )
    return cursor_ops.gas_cost(fork)


def calculate_benchmark_params(
    fork: Fork,
    gas_per_item: int,
    extra_overhead: int | None = None,
) -> tuple[int, int, int, int]:
    """Return (num_transactions, items_per_tx, total_items, max_tx_gas)."""
    gas_costs = fork.gas_costs()
    max_tx_gas = fork.transaction_gas_limit_cap()
    assert max_tx_gas is not None

    env = Environment()
    block_gas_limit = int(env.gas_limit)

    if extra_overhead is None:
        extra_overhead = cursor_overhead_gas(fork)

    num_transactions = block_gas_limit // max_tx_gas
    available_gas = max_tx_gas - gas_costs.G_TRANSACTION - extra_overhead
    items_per_tx = available_gas // gas_per_item
    total_items = num_transactions * items_per_tx
    return num_transactions, items_per_tx, total_items, max_tx_gas


def build_cursor_storage_changes(
    num_transactions: int,
    items_per_tx: int,
) -> list[BalStorageSlot]:
    """Build BAL storage-change entries for the cursor slot."""
    return [
        BalStorageSlot(
            slot=CURSOR_SLOT,
            slot_changes=[
                BalStorageChange(
                    block_access_index=tx_idx + 1,
                    post_value=(tx_idx + 1) * items_per_tx,
                )
                for tx_idx in range(num_transactions)
            ],
        ),
    ]


def build_contract_expectation(
    num_transactions: int,
    items_per_tx: int,
    data_slot_reads: list[int],
) -> BalAccountExpectation:
    """
    Build BAL expectations for a cursor-based benchmark contract.

    ``data_slot_reads`` should list every read-only slot beyond
    ITEMS_PER_TX_SLOT (which is auto-included).
    """
    all_reads = sorted(set(data_slot_reads + [ITEMS_PER_TX_SLOT]))
    return BalAccountExpectation(
        storage_reads=all_reads,
        storage_changes=build_cursor_storage_changes(
            num_transactions, items_per_tx
        ),
    )


def run_bal_benchmark(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    contract_code: Bytecode,
    contract_storage: Storage,
    num_transactions: int,
    items_per_tx: int,
    gas_limit: int,
    contract_expectation: BalAccountExpectation,
    post_contract: Account | None = None,
    extra_expectations: dict[Address, BalAccountExpectation] | None = None,
) -> None:
    """Run a single-contract cursor-based BAL benchmark test."""
    contract = pre.deploy_contract(
        code=contract_code, storage=contract_storage
    )

    senders = [pre.fund_eoa() for _ in range(num_transactions)]
    transactions = [
        Transaction(
            sender=senders[i],
            to=contract,
            gas_limit=gas_limit,
            data=b"",
        )
        for i in range(num_transactions)
    ]

    account_expectations: dict[Address, BalAccountExpectation] = {
        contract: contract_expectation,
    }
    for tx_idx, sender in enumerate(senders):
        account_expectations[sender] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=tx_idx + 1, post_nonce=1)
            ],
        )
    if extra_expectations:
        account_expectations.update(extra_expectations)

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    if post_contract is None:
        final_storage = dict(contract_storage)  # type: ignore[arg-type]
        final_storage[CURSOR_SLOT] = num_transactions * items_per_tx
        post_contract = Account(storage=Storage(final_storage))

    post: dict[Address, Account] = {contract: post_contract}
    for sender in senders:
        post[sender] = Account(nonce=1)

    blockchain_test(pre=pre, blocks=[block], post=post)
