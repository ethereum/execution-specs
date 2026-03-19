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
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Op,
    Storage,
    TestPhaseManager,
    Transaction,
)

# Dedicated storage slots for the cursor mechanism.
# PUSH3-sized values, safely above max data slots (~300 000).
CURSOR_SLOT = 0x100000
ITEMS_PER_TX_SLOT = 0x100001
COMPUTE_ITERS_SLOT = 0x100002


def cursor_read() -> Bytecode:
    """Read CURSOR_SLOT and ITEMS_PER_TX_SLOT from storage."""
    return (
        Op.PUSH3(CURSOR_SLOT)
        + Op.SLOAD
        + Op.PUSH3(ITEMS_PER_TX_SLOT)
        + Op.SLOAD
    )


def cursor_write() -> Bytecode:
    """Write updated cursor back to CURSOR_SLOT."""
    return Op.PUSH3(CURSOR_SLOT) + Op.SSTORE


def cursor_overhead_gas(fork: Fork) -> int:
    """
    Return gas overhead per TX for cursor reads + write.

    Two cold SLOADs (CURSOR_SLOT, ITEMS_PER_TX_SLOT) + one cold
    SSTORE (CURSOR_SLOT writeback) + associated POP/STOP.
    """
    overhead = cursor_read() + cursor_write() + Op.POP + Op.STOP
    return overhead.gas_cost(fork)


def sload_loop_iteration(
    loop_start: int = 0,
    loop_end: int = 0,
) -> Bytecode:
    """
    Return bytecode for one sequential-SLOAD loop iteration.

    Pass loop_start/loop_end for contract assembly; omit them
    (defaults to 0) when calling ``.gas_cost(fork)``.
    """
    return (
        Op.JUMPDEST
        + Op.DUP1
        + Op.ISZERO
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        + Op.DUP2
        + Op.SLOAD
        + Op.POP
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.ADD
        + Op.SWAP1
        + Op.PUSH1(0x01)
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH2(loop_start)
        + Op.JUMP
    )


def run_benchmark(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    contract_code: Bytecode,
    contract_storage: Storage,
    num_transactions: int,
    items_per_tx: int,
    gas_limit: int,
    post_contract: Account | None = None,
) -> None:
    """Run a single-contract cursor-based benchmark test."""
    contract = pre.deploy_contract(
        code=contract_code, storage=contract_storage
    )

    with TestPhaseManager.execution():
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

    if post_contract is None:
        final_storage = dict(contract_storage)  # type: ignore[arg-type]
        final_storage[CURSOR_SLOT] = num_transactions * items_per_tx
        post_contract = Account(storage=Storage(final_storage))

    post: dict[Address, Account] = {contract: post_contract}
    for sender in senders:
        post[sender] = Account(nonce=1)

    benchmark_test(pre=pre, post=post, blocks=[Block(txs=transactions)])
