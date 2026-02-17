"""
Benchmark blocks with block access list (BAL) storage dependencies.

All tests use different-sender transactions calling a shared contract
that reads and writes storage slot 0, creating a serial dependency
chain. Without BALs, a client sees independent senders and may assume
the transactions are parallelizable. With BALs, the client detects
the shared storage conflict and can schedule accordingly.

The ``tx_gas_fraction`` parameter controls the tradeoff between
scheduling overhead and computation throughput: low fractions produce
many small transactions (stress-testing scheduling), while high
fractions produce few large transactions (stress-testing computation).
"""

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
    "tx_gas_fraction",
    [
        pytest.param(0.0, id="min_per_tx_gas"),
        pytest.param(0.005, id="0.5pct_tx_gas_limit"),
        pytest.param(0.01, id="1pct_tx_gas_limit"),
        pytest.param(0.1, id="10pct_tx_gas_limit"),
        pytest.param(1.0, id="full_tx_gas_limit"),
    ],
)
def test_parallel_execution(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_gas_fraction: float,
) -> None:
    """
    Benchmark parallel execution with serial storage dependencies.

    Deploy a contract that initializes storage slot 0 to 1. Each
    execution transaction SLOADs slot 0, performs a keccak256 hash
    chain (iteration count determined by available gas), and SSTOREs
    the result back. A gas-check loop exits gracefully before OOG to
    preserve the SSTORE commit.

    The ``tx_gas_fraction`` parameter controls per-tx gas as a
    fraction of ``tx_gas_limit``. At 0.0, transactions use the
    minimum gas needed (maximizing tx count and scheduling overhead).
    At 1.0, a single transaction consumes the full gas limit
    (maximizing computation per tx).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # --- Gas cost calculation ---
    #
    # The While loop generates:
    #   JUMPDEST | body | condition | PC PUSH4 SUB JUMPI
    #
    # Per iteration gas (between consecutive GAS checks):
    #   body_gas + GT(3) + PC(2) + PUSH4(3) + SUB(3) + JUMPI(10)
    #   + JUMPDEST(1) + PUSH(3) + GAS(2) = body_gas + 27
    #
    # Exit path (condition fails to cleanup):
    #   GT(3) + PC(2) + PUSH4(3) + SUB(3) + JUMPI(10) = 21
    #
    # reserve_gas >= cleanup_gas + 21 ensures enough gas
    # remains after loop exit to complete the SSTORE.

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
            # Placeholder values: actual current_value/new_value differ
            # per tx, but gas cost is identical (nonzero -> nonzero).
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = keccak_body.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)

    reserve_gas = cleanup_gas + 50

    runtime_code = _build_keccak_chain_code(reserve_gas)

    per_iter_effective = body_gas + 27

    # Minimum per-tx gas: enough for setup + 1 keccak + cleanup.
    min_per_tx_gas = (
        intrinsic_gas + setup_gas + per_iter_effective + reserve_gas - 21
    )

    if tx_gas_fraction == 0.0:
        per_tx_gas = min_per_tx_gas
    else:
        per_tx_gas = max(
            min_per_tx_gas,
            int(tx_gas_limit * tx_gas_fraction),
        )
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

    contract_address = compute_create_address(address=deployer, nonce=0)

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
