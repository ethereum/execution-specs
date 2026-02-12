"""
Benchmark block level access lists with sequential keccak hash chains.

Each transaction reads storage slot 0, computes a keccak256 hash chain,
and writes the result back. This creates a data dependency between
transactions that prevents parallel execution.

The contract initializes storage slot 0 to 1 during deployment (to avoid
zero-to-nonzero SSTORE costs during the benchmark). Each execution
transaction loads this value into memory, repeatedly hashes it via
keccak256, and stores the final hash back. The next transaction depends
on the result, forming a serial chain.

The iteration count is controlled by the transaction gas limit: a
gas-check loop exits when remaining gas is insufficient for another
iteration, then commits the result via SSTORE.
"""

# TODO:
# Make test depend on the gas benchmark
# Find the correct folder layout
# Check with EEST team if we want to label BAL
# performance benchmarks for what they are supposed to test:
# VALID blocks:
# - Parallel execution
# - Storage prefetchers (this likely has to be done on top of big state)
# - Parallel state root calculation
# INVALID blocks
# - verifying if the block gets rejected quickly

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Initcode,
    Op,
    TestPhaseManager,
    Transaction,
    While,
    compute_create_address,
)


def _build_keccak_chain_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code for a keccak256 hash chain contract.

    Memory layout: [0:32] = hash value.

    Algorithm:
    1. SLOAD(0) -> memory[0:32]
    2. Loop while gas > reserve: memory[0:32] = keccak256(memory[0:32])
    3. SSTORE(0, memory[0:32])
    """
    setup = Op.MSTORE(
        0,
        Op.SLOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    keccak_body = Op.MSTORE(
        0,
        Op.SHA3(0, 32, data_size=32),
        old_memory_size=32,
        new_memory_size=32,
    )

    condition = Op.GT(Op.GAS, reserve_gas)

    loop = While(body=keccak_body, condition=condition)

    cleanup = (
        Op.SSTORE(
            0,
            Op.MLOAD(0),
            key_warm=True,
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    return setup + loop + cleanup


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "num_keccak_calls",
    [
        pytest.param(1, id="1_keccak"),
        pytest.param(10, id="10_keccaks"),
        pytest.param(100, id="100_keccaks"),
        pytest.param(1000, id="1k_keccaks"),
        pytest.param(0, id="max_keccaks"),
        # TODO: do not hardcode these constants
        # But make them a fraction of the gas benchmarks
        # This test should also target the 1 keccak,
        # This maxizes the amount of txs
        # It will be interesting to see
        # what test will perform the fastest
        # (if we normalize the amount of KECCAK calls)
    ],
)
def test_bal_keccak_chain(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    num_keccak_calls: int,
) -> None:
    """
    Benchmark sequential keccak hash chains preventing parallelization.

    Deploy a contract that initializes storage slot 0 to 1. Each execution
    transaction loads storage[0], hashes it N times via keccak256, and
    stores the result back. The next transaction reads the updated value,
    forming a sequential dependency chain.

    The gas-check loop ensures the transaction never runs out of gas
    before committing the SSTORE. The number of keccak calls is
    controlled by the transaction gas limit.
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # --- Gas cost calculation ---
    #
    # Setup: MSTORE(0, SLOAD(0))
    # Body:  MSTORE(0, SHA3(0, 32))
    # Cleanup: SSTORE(0, MLOAD(0)) + STOP
    #
    # The While loop generates:
    #   JUMPDEST | body | condition | PC PUSH4 SUB JUMPI
    #
    # Condition = GT(GAS, reserve) generates: PUSH(reserve) GAS GT
    #
    # Per iteration gas between consecutive GAS checks:
    #   GT(3) + PC(2) + PUSH4(3) + SUB(3) + JUMPI(10)
    #   + JUMPDEST(1) + body_gas + PUSH(3) + GAS(2) = 27 + body_gas
    #
    # Initial path (setup to first GAS check):
    #   setup_gas + JUMPDEST(1) + body_gas + PUSH(3) + GAS(2) = setup_gas
    #   + body_gas + 6
    #
    # Exit path (GAS check fails to cleanup):
    #   GT(3) + PC(2) + PUSH4(3) + SUB(3) + JUMPI(10) = 21
    #
    # For N iterations, the GAS value at check N:
    #   V_N = V_1 - (N-1) * (body_gas + 27)
    #   V_1 = G - setup_gas - body_gas - 6
    #   where G = per_tx_gas - intrinsic_gas
    #
    # Loop exits when V_N <= reserve_gas. After exit, remaining gas
    # for cleanup: V_N - 21 >= cleanup_gas.
    # So reserve_gas >= cleanup_gas + 21.

    setup = Op.MSTORE(
        0,
        Op.SLOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    keccak_body = Op.MSTORE(
        0,
        Op.SHA3(0, 32, data_size=32),
        old_memory_size=32,
        new_memory_size=32,
    )

    cleanup = (
        Op.SSTORE(
            0,
            Op.MLOAD(0),
            key_warm=True,
            # Note: these values are incorrect, but
            # the gas calculation situation is the same
            # (changes nonzero value to a different nonzero value)
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = keccak_body.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)

    # Reserve: enough for exit path + cleanup + safety margin.
    reserve_gas = cleanup_gas + 50

    # Build the actual runtime code with computed reserve.
    runtime_code = _build_keccak_chain_code(reserve_gas)

    # Per-iteration effective gas (between consecutive GAS checks).
    per_iter_effective = body_gas + 27

    # --- Compute per-tx gas for N keccak calls ---
    #
    # Setting V_N = reserve_gas (loop exits after exactly N iterations):
    #   G = setup_gas + body_gas + 6 + reserve_gas + (N-1)*(body_gas + 27)
    #     = setup_gas + N*(body_gas + 27) + reserve_gas - 21
    #
    # per_tx_gas = intrinsic + G

    if num_keccak_calls == 0:
        # Max: use full tx gas limit, compute N from available gas.
        per_tx_gas = tx_gas_limit
        execution_gas = per_tx_gas - intrinsic_gas
        num_keccak_calls = max(
            1,
            (execution_gas - setup_gas - reserve_gas + 21)
            // per_iter_effective,
        )
    else:
        execution_gas = (
            setup_gas
            + num_keccak_calls * per_iter_effective
            + reserve_gas
            - 21
        )
        per_tx_gas = intrinsic_gas + execution_gas
        per_tx_gas = min(per_tx_gas, tx_gas_limit)

    # --- Deploy contract ---
    creation_code = Initcode(
        deploy_code=runtime_code,
        initcode_prefix=Op.SSTORE(0, 1),
    )

    blocks = []

    with TestPhaseManager.setup():
        deployer = pre.fund_eoa()
        deploy_tx = Transaction(
            to=None,
            gas_limit=tx_gas_limit,
            data=creation_code,
            sender=deployer,
        )
        blocks.append(Block(txs=[deploy_tx]))

    contract_address = compute_create_address(
        address=deployer, nonce=0
    )

    # --- Execution block: fill with sequential transactions ---
    num_exec_txs = max(1, gas_benchmark_value // per_tx_gas)

    with TestPhaseManager.execution():
        exec_txs = []
        for _ in range(num_exec_txs):
            exec_txs.append(
                Transaction(
                    to=contract_address,
                    gas_limit=per_tx_gas,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks)
