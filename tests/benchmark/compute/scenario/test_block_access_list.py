"""
Benchmark blocks with block access list (BAL) storage dependencies.

Tests target different BAL optimization paths:

- ``test_parallel_execution``: Serial storage dependency (shared slot 0).
  Stress-tests conflict detection and scheduling.

- ``test_state_root_computation``: Independent txs writing disjoint
  storage slots. Stress-tests trie update spread during post-execution
  root hashing.

The ``tx_count_fraction`` parameter controls the scheduling/computation
tradeoff across all tests.
"""

import math

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
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


def _build_sequential_sstore_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code that SSTOREs to sequential cold storage slots.

    Read ``start_slot`` from ``calldata[0:32]``, then loop writing a
    constant nonzero value to ``slot``, ``slot + 1``, ... until
    remaining gas drops below ``reserve_gas``.

    Memory layout: ``[0:32]`` = current slot counter.
    """
    setup = Op.MSTORE(
        0,
        Op.CALLDATALOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    sstore_body = Op.SSTORE(
        Op.MLOAD(0),
        42,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=42,
    ) + Op.MSTORE(
        0,
        Op.ADD(Op.MLOAD(0), 1),
        old_memory_size=32,
        new_memory_size=32,
    )

    condition = Op.GT(Op.GAS, reserve_gas)

    loop = While(body=sstore_body, condition=condition)

    return setup + loop + Op.STOP


def _derive_tx_schedule(
    gas_benchmark_value: int,
    min_per_tx_gas: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
) -> tuple[int, int]:
    """
    Derive tx count and per-tx gas from a fraction of maximum txs.

    Return ``(num_txs, per_tx_gas)`` where ``num_txs`` is the number
    of transactions and ``per_tx_gas`` is the gas limit per tx.
    """
    max_num_txs = gas_benchmark_value // min_per_tx_gas
    if tx_count_fraction == 0.0:
        num_txs = 1
    else:
        num_txs = max(1, int(max_num_txs * tx_count_fraction))
    per_tx_gas = min(tx_gas_limit, gas_benchmark_value // num_txs)
    return num_txs, per_tx_gas


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "tx_count_fraction",
    [
        pytest.param(0.0, id="1_tx"),
        pytest.param(0.01, id="1pct_max_txs"),
        pytest.param(0.1, id="10pct_max_txs"),
        pytest.param(0.5, id="50pct_max_txs"),
        pytest.param(1.0, id="max_txs"),
    ],
)
def test_parallel_execution(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
) -> None:
    """
    Benchmark parallel execution with serial storage dependencies.

    Deploy a contract that initializes storage slot 0 to 1. Each
    execution transaction SLOADs slot 0, performs a keccak256 hash
    chain (iteration count determined by available gas), and SSTOREs
    the result back. A gas-check loop exits gracefully before OOG to
    preserve the SSTORE commit.

    The ``tx_count_fraction`` parameter controls the number of
    transactions as a fraction of the maximum that fit in the gas
    budget. At 0.0, a single transaction consumes as much gas as
    ``tx_gas_limit`` allows. At 1.0, the block is packed with the
    maximum number of minimum-gas transactions.
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

    num_exec_txs, per_tx_gas = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_count_fraction
    )

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

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "contract_per_tx",
    [
        pytest.param(False, id="single_contract"),
        pytest.param(True, id="contract_per_tx"),
    ],
)
@pytest.mark.parametrize(
    "tx_count_fraction",
    [
        pytest.param(0.0, id="1_tx"),
        pytest.param(0.01, id="1pct_max_txs"),
        pytest.param(0.1, id="10pct_max_txs"),
        pytest.param(0.5, id="50pct_max_txs"),
        pytest.param(1.0, id="max_txs"),
    ],
)
def test_state_root_computation(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
    contract_per_tx: bool,
) -> None:
    """
    Benchmark state root computation with disjoint storage writes.

    Deploy contracts with pre-populated storage. Each execution
    transaction writes to a non-overlapping range of sequential cold
    storage slots via a gas-check loop, so all transactions are
    genuinely independent.

    The ``tx_count_fraction`` parameter controls the number of
    transactions as a fraction of the maximum that fit in the gas
    budget. The ``contract_per_tx`` parameter controls whether each
    transaction targets a unique contract (maximizing account trie
    width) or all transactions share a single contract (maximizing
    storage trie depth).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    # Worst-case calldata cost: 32 nonzero bytes.
    intrinsic_gas = intrinsic_gas_calculator(calldata=b"\xff" * 32)

    # --- Gas cost calculation ---
    #
    # All costs derived from .gas_cost(fork); no hardcoded constants.

    setup = Op.MSTORE(
        0,
        Op.CALLDATALOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    sstore_body = Op.SSTORE(
        Op.MLOAD(0),
        42,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=42,
    ) + Op.MSTORE(
        0,
        Op.ADD(Op.MLOAD(0), 1),
        old_memory_size=32,
        new_memory_size=32,
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = sstore_body.gas_cost(fork)

    # Derive per-iteration gas from the While loop structure.
    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=sstore_body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    # Exit overhead: condition + jump logic consumed when the loop
    # condition fails (everything except JUMPDEST and body).
    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    cleanup_gas = Op.STOP.gas_cost(fork)
    # reserve_gas must cover a full iteration so the loop only
    # re-enters when enough gas remains for another body + exit.
    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_sequential_sstore_code(reserve_gas)

    # Minimum per-tx gas: intrinsic + setup + one full loop iteration.
    min_per_tx_gas = intrinsic_gas + setup_gas + per_iter_gas

    num_exec_txs, per_tx_gas = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_count_fraction
    )

    # --- Estimate slots written per tx (for storage pre-population) ---
    available_gas = per_tx_gas - intrinsic_gas - setup_gas
    estimated_slots_per_tx = max(1, available_gas // per_iter_gas)

    # --- Deploy contracts ---
    num_contracts = num_exec_txs if contract_per_tx else 1
    txs_per_contract = math.ceil(num_exec_txs / num_contracts)
    slots_per_contract = (estimated_slots_per_tx + 1) * txs_per_contract

    contracts = []
    for _ in range(num_contracts):
        addr = pre.deploy_contract(
            code=runtime_code,
            storage=dict.fromkeys(range(slots_per_contract), 1),
        )
        contracts.append(addr)

    # --- Execution block: distribute txs across contracts ---
    blocks: list[Block] = []
    contract_tx_counts = [0] * num_contracts

    with TestPhaseManager.execution():
        exec_txs = []
        for tx_idx in range(num_exec_txs):
            c_idx = tx_idx % num_contracts
            start_slot = contract_tx_counts[c_idx] * estimated_slots_per_tx
            contract_tx_counts[c_idx] += 1
            exec_txs.append(
                Transaction(
                    to=contracts[c_idx],
                    gas_limit=per_tx_gas,
                    data=Hash(start_slot),
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)
