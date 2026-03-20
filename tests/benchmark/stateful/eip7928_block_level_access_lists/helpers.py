"""
Shared constants and helpers for BAL benchmark tests.

All cursor-based BAL benchmarks follow the same pattern:
1. Contract reads a cursor from CURSOR_SLOT to know where to start.
2. Contract loops while remaining gas exceeds a threshold.
3. Contract writes the updated cursor back to CURSOR_SLOT.

Every transaction sends empty calldata; the cursor in storage
tracks progress.  TX N writes CURSOR_SLOT, TX N+1 reads it,
creating a genuine inter-transaction dependency that requires
the BAL for parallel execution.

Contracts use a gas-check loop: at the top of each iteration the
contract executes ``GAS > threshold`` and exits when the remaining
gas is too low for another iteration plus teardown (SSTORE).  This
avoids pre-calculating iteration counts and lets the last
transaction in a block naturally do fewer iterations.
"""

from __future__ import annotations

from dataclasses import dataclass

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

# Dedicated storage slots for the cursor mechanism.
# PUSH3-sized values, safely above max data slots (~300 000).
CURSOR_SLOT = 0x100000
COMPUTE_ITERS_SLOT = 0x100002


# ---------------------------------------------------------------------------
# Bytecode helpers
# ---------------------------------------------------------------------------


def cursor_read() -> Bytecode:
    """Read CURSOR_SLOT from storage (stack: [...] -> [..., cursor])."""
    return Op.PUSH3(CURSOR_SLOT) + Op.SLOAD


def cursor_write() -> Bytecode:
    """Write cursor from stack to CURSOR_SLOT."""
    return Op.PUSH3(CURSOR_SLOT) + Op.SSTORE


def default_teardown() -> Bytecode:
    """Standard loop teardown: write cursor and stop."""
    return Op.JUMPDEST + cursor_write() + Op.STOP


def sload_loop_body() -> Bytecode:
    """
    Return the SLOAD loop body (no loop control).

    Stack on entry:  [ignored, cursor]
    Stack on exit:   [ignored, cursor+1]
    Side-effect:     SLOAD(cursor) result discarded.
    """
    return (
        Op.DUP1
        + Op.SLOAD
        + Op.POP
        + Op.PUSH1(0x01)
        + Op.ADD
    )


# ---------------------------------------------------------------------------
# Gas-cost helpers (all derived from bytecode, no hardcoded values)
# ---------------------------------------------------------------------------


def _loop_overhead_gas(fork: Fork) -> int:
    """
    Gas overhead per iteration for gas-check loop control flow.

    Header:  JUMPDEST + GAS + PUSH3 + GT + ISZERO + PUSH2 + JUMPI
    Footer:  PUSH2 + JUMP
    """
    header = (
        Op.JUMPDEST
        + Op.GAS
        + Op.PUSH3(0)
        + Op.GT
        + Op.ISZERO
        + Op.PUSH2(0)
        + Op.JUMPI
    )
    footer = Op.PUSH2(0) + Op.JUMP
    return header.gas_cost(fork) + footer.gas_cost(fork)


def _gas_opcode_offset(fork: Fork) -> int:
    """
    Gas consumed before the GAS opcode returns its value.

    At the top of the loop: JUMPDEST + GAS.  The value pushed
    by GAS equals ``remaining - cost(JUMPDEST) - cost(GAS)``.
    """
    return (Op.JUMPDEST + Op.GAS).gas_cost(fork)


def compute_gas_threshold(
    fork: Fork,
    loop_body_gas: int,
    teardown: Bytecode | None = None,
) -> int:
    """
    Compute the gas threshold for a gas-check loop.

    The threshold must be high enough that when ``GAS > threshold``
    is true, there is sufficient gas for one more loop body, the
    loop overhead, and the teardown (SSTORE + STOP).  When
    ``GAS <= threshold`` the remaining gas still covers the exit
    check and teardown.

    Pass *teardown* when the loop teardown differs from the
    default (``JUMPDEST + cursor_write + STOP``).
    """
    if teardown is None:
        teardown = default_teardown()
    overhead = _loop_overhead_gas(fork)
    teardown_gas = teardown.gas_cost(fork)
    return loop_body_gas + overhead + teardown_gas


def expected_iterations(
    fork: Fork,
    tx_gas: int,
    intrinsic_gas: int,
    setup_gas: int,
    gas_threshold: int,
    iteration_gas: int,
) -> int:
    """
    Compute the expected number of loop iterations for a single tx.

    The gas-check loop continues while ``GAS > threshold``.
    The GAS opcode returns ``remaining - gas_opcode_offset``,
    so the loop exits when
    ``remaining <= threshold + gas_opcode_offset``.
    Each iteration consumes *iteration_gas* (body + overhead).
    """
    offset = _gas_opcode_offset(fork)
    starting = tx_gas - intrinsic_gas - setup_gas
    if starting <= gas_threshold + offset:
        return 0
    return (
        (starting - gas_threshold - offset - 1)
        // iteration_gas
        + 1
    )


# ---------------------------------------------------------------------------
# Transaction planning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkPlan:
    """Pre-computed plan for a gas-check-loop benchmark."""

    gas_limits: list[int]
    iterations_per_tx: list[int]
    total_iterations: int
    gas_threshold: int
    iteration_gas: int


def plan_benchmark(
    fork: Fork,
    loop_body_gas: int,
    setup_gas: int,
    teardown: Bytecode | None = None,
    num_transactions: int | None = None,
    tx_gas_limit: int | None = None,
) -> BenchmarkPlan:
    """
    Plan transactions for a gas-check-loop benchmark.

    For full-scale benchmarks (no overrides) the block is filled
    with as many transactions as fit.  The last transaction receives
    whatever gas remains in the block.

    For simple tests, pass *num_transactions* and *tx_gas_limit*.

    Pass *teardown* when the loop teardown differs from the
    default (``JUMPDEST + cursor_write + STOP``).
    """
    gas_threshold = compute_gas_threshold(
        fork, loop_body_gas, teardown
    )
    overhead = _loop_overhead_gas(fork)
    iteration_gas = loop_body_gas + overhead
    intrinsic_gas = fork.gas_costs().G_TRANSACTION
    offset = _gas_opcode_offset(fork)

    # Minimum gas for a useful tx: intrinsic + setup + threshold
    # + gas_opcode_offset + 1 (for strict >).
    min_useful_gas = (
        intrinsic_gas + setup_gas + gas_threshold + offset + 1
    )

    if num_transactions is not None and tx_gas_limit is not None:
        gas_limits = [tx_gas_limit] * num_transactions
    else:
        max_tx_gas = fork.transaction_gas_limit_cap()
        assert max_tx_gas is not None
        block_gas_limit = int(Environment().gas_limit)
        gas_limits = []
        remaining = block_gas_limit
        while remaining >= min_useful_gas:
            g = min(remaining, max_tx_gas)
            if g < min_useful_gas:
                break
            gas_limits.append(g)
            remaining -= g

    iters = [
        expected_iterations(
            fork,
            g,
            intrinsic_gas,
            setup_gas,
            gas_threshold,
            iteration_gas,
        )
        for g in gas_limits
    ]

    return BenchmarkPlan(
        gas_limits=gas_limits,
        iterations_per_tx=iters,
        total_iterations=sum(iters),
        gas_threshold=gas_threshold,
        iteration_gas=iteration_gas,
    )


# ---------------------------------------------------------------------------
# BAL expectation builders
# ---------------------------------------------------------------------------


def build_cursor_storage_changes(
    iterations_per_tx: list[int],
) -> list[BalStorageSlot]:
    """Build BAL storage-change entries for the cursor slot."""
    cumulative = 0
    changes: list[BalStorageChange] = []
    for tx_idx, iters in enumerate(iterations_per_tx):
        cumulative += iters
        changes.append(
            BalStorageChange(
                block_access_index=tx_idx + 1,
                post_value=cumulative,
            )
        )
    return [
        BalStorageSlot(slot=CURSOR_SLOT, slot_changes=changes)
    ]


def build_contract_expectation(
    iterations_per_tx: list[int],
    data_slot_reads: list[int],
) -> BalAccountExpectation:
    """
    Build BAL expectations for a cursor-based benchmark contract.

    *data_slot_reads* should list every read-only slot accessed by
    the contract beyond the cursor slot itself.
    """
    return BalAccountExpectation(
        storage_reads=sorted(set(data_slot_reads)),
        storage_changes=build_cursor_storage_changes(
            iterations_per_tx
        ),
    )


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def run_bal_benchmark(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    contract_code: Bytecode,
    contract_storage: Storage,
    plan: BenchmarkPlan,
    data_slot_reads: list[int] | None = None,
    post_contract: Account | None = None,
    extra_expectations: (
        dict[Address, BalAccountExpectation] | None
    ) = None,
) -> None:
    """Run a single-contract cursor-based BAL benchmark test."""
    contract = pre.deploy_contract(
        code=contract_code, storage=contract_storage
    )

    num_txs = len(plan.gas_limits)
    with TestPhaseManager.execution():
        senders = [pre.fund_eoa() for _ in range(num_txs)]
        transactions = [
            Transaction(
                sender=senders[i],
                to=contract,
                gas_limit=plan.gas_limits[i],
                data=b"",
            )
            for i in range(num_txs)
        ]

    # BAL expectations.
    account_expectations: dict[
        Address, BalAccountExpectation
    ] = {
        contract: build_contract_expectation(
            plan.iterations_per_tx,
            data_slot_reads or [],
        ),
    }
    for tx_idx, sender in enumerate(senders):
        account_expectations[sender] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=tx_idx + 1,
                    post_nonce=1,
                )
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

    # Post-state.
    if post_contract is None:
        final_storage = dict(
            contract_storage
        )  # type: ignore[arg-type]
        final_storage[CURSOR_SLOT] = plan.total_iterations
        post_contract = Account(
            storage=Storage(final_storage)
        )

    post: dict[Address, Account] = {contract: post_contract}
    for sender in senders:
        post[sender] = Account(nonce=1)

    benchmark_test(pre=pre, post=post, blocks=[block])
