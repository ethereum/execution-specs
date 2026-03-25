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

CURSOR_SLOT = 0
CURSOR_INIT = 1


def cursor_read() -> Bytecode:
    """PUSH1(CURSOR_SLOT) + SLOAD → stack: [..., cursor]."""
    return Op.PUSH1(CURSOR_SLOT) + Op.SLOAD


def cursor_write() -> Bytecode:
    """
    PUSH1(CURSOR_SLOT) + SSTORE ← stack: [..., cursor].

    SSTORE metadata reflects runtime: cursor slot is warm
    (setup SLOADs it) and nonzero-to-nonzero.
    """
    return Op.PUSH1(CURSOR_SLOT) + Op.SSTORE(
        key_warm=True,
        original_value=1,
        current_value=1,
        new_value=2,
    )


def default_teardown() -> Bytecode:
    """Standard loop teardown: write cursor and stop."""
    return Op.JUMPDEST + cursor_write() + Op.STOP


def sload_loop_body() -> Bytecode:
    """SLOAD(cursor) then cursor++ (result discarded)."""
    return Op.DUP1 + Op.SLOAD + Op.POP + Op.PUSH1(0x01) + Op.ADD


def sload_loop_body_reverse() -> Bytecode:
    """SLOAD(cursor) then cursor-- (result discarded)."""
    return Op.DUP1 + Op.SLOAD + Op.POP + Op.PUSH1(0x01) + Op.SWAP1 + Op.SUB


# -- Gas-check loop components -- #
# Used by both gas_check_loop_contract (assembly) and plan_benchmark
# (gas estimation).  Operand values are irrelevant for gas costs.


def _pre_gas_header(gas_threshold: int = 0) -> Bytecode:
    """Loop header prefix consumed before GAS reports."""
    return Op.JUMPDEST + Op.PUSH3(gas_threshold) + Op.GAS


def _loop_header(gas_threshold: int = 0) -> Bytecode:
    """Full loop condition: JUMPDEST PUSH3 GAS GT ISZERO."""
    return _pre_gas_header(gas_threshold) + Op.GT + Op.ISZERO


def _loop_exit(target: int = 0) -> Bytecode:
    """Exit jump when loop condition fails."""
    return Op.PUSH2(target) + Op.JUMPI


def _loop_back(target: int = 0) -> Bytecode:
    """Back-edge jump to loop start."""
    return Op.PUSH2(target) + Op.JUMP


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
    header = _loop_header(gas_threshold)
    loop_end = (
        loop_start
        + len(header)
        + len(_loop_exit())
        + len(body)
        + len(_loop_back())
    )

    return (
        setup
        + header
        + _loop_exit(loop_end)
        + body
        + _loop_back(loop_start)
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
    gas_benchmark_value: int,
    teardown: Bytecode | None = None,
    num_transactions: int | None = None,
    tx_gas_limit: int | None = None,
) -> BenchmarkPlan:
    """
    Plan transactions for a gas-check-loop benchmark.

    Fill up to *gas_benchmark_value* total gas with transactions.
    The last transaction gets whatever gas remains.  Pass *teardown*
    when it differs from ``default_teardown()``.
    """
    if teardown is None:
        teardown = default_teardown()

    overhead = (
        _loop_header().gas_cost(fork)
        + _loop_exit().gas_cost(fork)
        + _loop_back().gas_cost(fork)
    )
    teardown_gas = teardown.gas_cost(fork)
    gas_opcode_offset = _pre_gas_header().gas_cost(fork)

    gas_threshold = loop_body_gas + overhead + teardown_gas
    iteration_gas = loop_body_gas + overhead
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    min_useful = (
        intrinsic_gas + setup_gas + gas_threshold + gas_opcode_offset + 1
    )
    gas_limits: list[int] = []
    # Build per-tx gas limits.
    if num_transactions is not None and tx_gas_limit is not None:
        gas_limits = [tx_gas_limit] * num_transactions
    else:
        max_tx_gas = fork.transaction_gas_limit_cap()
        assert max_tx_gas is not None
        remaining = gas_benchmark_value
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
            avail - gas_threshold - gas_opcode_offset - 1
        ) // iteration_gas + 1

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
    extra_expectations: (dict[Address, BalAccountExpectation] | None) = None,
) -> None:
    """Deploy contract, create txs, BAL expectations, and run."""
    contract = pre.deploy_contract(
        code=contract_code, storage=contract_storage
    )

    num_txs = len(plan.gas_limits)
    with TestPhaseManager.execution():
        sender = pre.fund_eoa()
        transactions = [
            Transaction(
                sender=sender,
                to=contract,
                gas_limit=plan.gas_limits[i],
                data=b"",
            )
            for i in range(num_txs)
        ]

    # BAL expectations: contract slots + sender nonces.
    # Use validate_any_change for cursor — exact values depend
    # on gas dynamics and are verified by consensus test suites.
    # All txs share a single sender to prevent trivial per-sender
    # optimizations in BAL implementations.
    expectations: dict[Address, BalAccountExpectation] = {
        contract: BalAccountExpectation(
            storage_reads=sorted(set(data_slot_reads or [])),
            storage_changes=[
                BalStorageSlot(
                    slot=CURSOR_SLOT,
                    validate_any_change=True,
                )
            ],
        ),
        sender: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=tx_idx + 1,
                    post_nonce=tx_idx + 1,
                )
                for tx_idx in range(num_txs)
            ],
        ),
    }
    if extra_expectations:
        expectations.update(extra_expectations)

    block = Block(
        txs=transactions,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=expectations
        ),
    )

    # Post-state: only check sender nonce (sanity).
    # Exact storage values depend on gas dynamics and may be
    # slightly off; consensus correctness is verified elsewhere.
    post: dict[Address, Account] = {
        sender: Account(nonce=num_txs),
    }

    benchmark_test(
        pre=pre, post=post, blocks=[block], skip_gas_used_validation=True
    )
