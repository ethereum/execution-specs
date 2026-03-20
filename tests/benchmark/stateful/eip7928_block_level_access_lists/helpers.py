"""
Shared helpers for EIP-7928 BAL benchmark tests.

Contracts use a gas-check loop: ``GAS > threshold`` at the top of
each iteration exits when remaining gas is too low for another
iteration plus teardown.  This avoids pre-calculating iteration
counts and lets the last transaction naturally do fewer iterations.
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

CURSOR_SLOT = 0
CURSOR_INIT = 1


def cursor_read() -> Bytecode:
    """PUSH1(CURSOR_SLOT) + SLOAD → stack: [..., cursor]."""
    return Op.PUSH1(CURSOR_SLOT) + Op.SLOAD


def cursor_write() -> Bytecode:
    """PUSH1(CURSOR_SLOT) + SSTORE ← stack: [..., cursor]."""
    return Op.PUSH1(CURSOR_SLOT) + Op.SSTORE


def default_teardown() -> Bytecode:
    """Standard loop teardown: write cursor and stop."""
    return Op.JUMPDEST + cursor_write() + Op.STOP


def sload_loop_body() -> Bytecode:
    """SLOAD(cursor) then cursor++ (result discarded)."""
    return (
        Op.DUP1
        + Op.SLOAD
        + Op.POP
        + Op.PUSH1(0x01)
        + Op.ADD
    )


def gas_check_loop_contract(
    setup: Bytecode,
    body: Bytecode,
    gas_threshold: int,
    teardown: Bytecode | None = None,
) -> Bytecode:
    """
    Assemble a contract with a gas-check loop.

    Structure: setup | JUMPDEST GAS>threshold? body JUMP | teardown.
    The loop exits when remaining gas is too low for another
    iteration plus teardown.
    """
    if teardown is None:
        teardown = default_teardown()

    loop_start = len(setup)
    header = (
        Op.JUMPDEST
        + Op.GAS
        + Op.PUSH3(gas_threshold)
        + Op.GT
        + Op.ISZERO
    )
    loop_end = (
        loop_start + len(header)
        + 3 + 1          # PUSH2(loop_end) + JUMPI
        + len(body)
        + 3 + 1          # PUSH2(loop_start) + JUMP
    )

    return (
        setup
        + header
        + Op.PUSH2(loop_end)
        + Op.JUMPI
        + body
        + Op.PUSH2(loop_start)
        + Op.JUMP
        + teardown
    )


@dataclass(frozen=True)
class BenchmarkPlan:
    """Pre-computed plan for a gas-check-loop benchmark."""

    gas_limits: list[int]
    iterations_per_tx: list[int]
    total_iterations: int
    gas_threshold: int


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

    Fills the block with transactions; the last one gets whatever
    gas remains.  For simple tests pass *num_transactions* and
    *tx_gas_limit*.  Pass *teardown* when it differs from
    ``default_teardown()``.
    """
    if teardown is None:
        teardown = default_teardown()

    # All gas costs derived from bytecode.
    loop_header = (
        Op.JUMPDEST + Op.GAS + Op.PUSH3(0)
        + Op.GT + Op.ISZERO + Op.PUSH2(0) + Op.JUMPI
    )
    loop_footer = Op.PUSH2(0) + Op.JUMP
    overhead = loop_header.gas_cost(fork) + loop_footer.gas_cost(fork)
    teardown_gas = teardown.gas_cost(fork)
    gas_opcode_offset = (Op.JUMPDEST + Op.GAS).gas_cost(fork)

    gas_threshold = loop_body_gas + overhead + teardown_gas
    iteration_gas = loop_body_gas + overhead
    intrinsic_gas = fork.gas_costs().G_TRANSACTION
    min_useful = (
        intrinsic_gas + setup_gas
        + gas_threshold + gas_opcode_offset + 1
    )

    # Build per-tx gas limits.
    if num_transactions is not None and tx_gas_limit is not None:
        gas_limits = [tx_gas_limit] * num_transactions
    else:
        max_tx_gas = fork.transaction_gas_limit_cap()
        assert max_tx_gas is not None
        block_gas = int(Environment().gas_limit)
        gas_limits: list[int] = []
        remaining = block_gas
        while remaining >= min_useful:
            g = min(remaining, max_tx_gas)
            if g < min_useful:
                break
            gas_limits.append(g)
            remaining -= g

    # Expected iterations per tx.
    def _iters(tx_gas: int) -> int:
        avail = tx_gas - intrinsic_gas - setup_gas
        if avail <= gas_threshold + gas_opcode_offset:
            return 0
        return (
            (avail - gas_threshold - gas_opcode_offset - 1)
            // iteration_gas + 1
        )

    iters = [_iters(g) for g in gas_limits]
    return BenchmarkPlan(
        gas_limits=gas_limits,
        iterations_per_tx=iters,
        total_iterations=sum(iters),
        gas_threshold=gas_threshold,
    )


def run_bal_benchmark(
    pre: Alloc,
    benchmark_test: BenchmarkTestFiller,
    contract_code: Bytecode,
    contract_storage: Storage,
    plan: BenchmarkPlan,
    data_slot_reads: list[int] | None = None,
    post_contract: Account | None = None,
    extra_expectations: (
        dict[Address, BalAccountExpectation] | None
    ) = None,
) -> None:
    """Deploy contract, create txs, BAL expectations, and run."""
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

    # BAL expectations: contract slots + sender nonces.
    cumulative = CURSOR_INIT
    cursor_changes: list[BalStorageChange] = []
    for tx_idx, iters in enumerate(plan.iterations_per_tx):
        cumulative += iters
        cursor_changes.append(
            BalStorageChange(
                block_access_index=tx_idx + 1,
                post_value=cumulative,
            )
        )

    expectations: dict[Address, BalAccountExpectation] = {
        contract: BalAccountExpectation(
            storage_reads=sorted(set(data_slot_reads or [])),
            storage_changes=[
                BalStorageSlot(
                    slot=CURSOR_SLOT,
                    slot_changes=cursor_changes,
                )
            ],
        ),
    }
    for tx_idx, sender in enumerate(senders):
        expectations[sender] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=tx_idx + 1,
                    post_nonce=1,
                )
            ],
        )
    if extra_expectations:
        expectations.update(extra_expectations)

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=expectations
        ),
    )

    # Post-state.
    if post_contract is None:
        final = dict(
            contract_storage
        )  # type: ignore[arg-type]
        final[CURSOR_SLOT] = CURSOR_INIT + plan.total_iterations
        post_contract = Account(storage=Storage(final))

    post: dict[Address, Account] = {contract: post_contract}
    for sender in senders:
        post[sender] = Account(nonce=1)

    benchmark_test(pre=pre, post=post, blocks=[block])
