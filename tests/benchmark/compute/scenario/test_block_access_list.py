"""
Benchmark blocks with block access list (BAL) storage dependencies.

Tests target different BAL optimization paths:

- Parallel execution: The ability for clients to execute transactions
  in parallel.
- State root computation: The ability for clients to compute the post-state
  root in parallel with execution.
- Cold storage prefetching: The ability for clients to prefetch cold
  storage slots in parallel with execution.
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
    Storage,
    TestPhaseManager,
    Transaction,
    While,
    compute_create_address,
)

from ethereum.crypto.hash import keccak256


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


def _build_keccak_chain_with_coinbase_code(reserve_gas: int) -> Bytecode:
    """
    Build keccak chain code with an explicit value transfer to coinbase.

    Same as ``_build_keccak_chain_code`` but inserts a
    ``CALL(gas=0, to=COINBASE, value=1)`` before the keccak loop.
    This makes the coinbase dependency visible in execution traces
    and triggers client-specific coinbase detection logic (e.g. Besu's
    ``TransactionCollisionDetector``).

    Coinbase is warm per EIP-3651 (Shanghai+).
    """
    setup = Op.MSTORE(
        0,
        Op.SLOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    coinbase_call = Op.POP(
        Op.CALL(
            gas=0,
            address=Op.COINBASE,
            value=1,
            address_warm=True,
            value_transfer=True,
        )
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

    return setup + coinbase_call + loop + cleanup


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


def _build_sequential_sload_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code that SLOADs sequential cold storage slots.

    Read ``start_slot`` from ``calldata[0:32]``, then loop reading
    ``slot``, ``slot + 1``, ... until remaining gas drops below
    ``reserve_gas``. Values are discarded (POP).

    Memory layout: ``[0:32]`` = current slot counter.
    """
    setup = Op.MSTORE(
        0,
        Op.CALLDATALOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    sload_body = Op.POP(
        Op.SLOAD(
            Op.MLOAD(0),
            key_warm=False,
        ),
    ) + Op.MSTORE(
        0,
        Op.ADD(Op.MLOAD(0), 1),
        old_memory_size=32,
        new_memory_size=32,
    )

    condition = Op.GT(Op.GAS, reserve_gas)

    loop = While(body=sload_body, condition=condition)

    return setup + loop + Op.STOP


def _build_hash_chain_sload_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code that SLOADs scattered cold storage slots.

    Read ``seed`` from ``calldata[0:32]``, then loop: compute
    ``slot = keccak256(slot)``, ``SLOAD(slot)``, discard value,
    repeat until remaining gas drops below ``reserve_gas``.

    Each slot depends on the previous keccak result, so the access
    pattern is unpredictable without a BAL but trivially prefetchable
    with one.

    Memory layout: ``[0:32]`` = current slot key.
    """
    setup = Op.MSTORE(
        0,
        Op.CALLDATALOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    hash_sload_body = Op.MSTORE(
        0,
        Op.SHA3(0, 32, data_size=32),
        old_memory_size=32,
        new_memory_size=32,
    ) + Op.POP(
        Op.SLOAD(
            Op.MLOAD(0),
            key_warm=False,
        ),
    )

    condition = Op.GT(Op.GAS, reserve_gas)

    loop = While(body=hash_sload_body, condition=condition)

    return setup + loop + Op.STOP


def _compute_hash_chain(seed: int, length: int) -> list[int]:
    """
    Compute a keccak256 hash chain of storage slot keys.

    Return a list of ``length`` slot keys where each key is
    ``keccak256`` of the previous (starting from ``seed``).
    """
    slots = []
    current = seed
    for _ in range(length):
        current = int.from_bytes(
            keccak256(current.to_bytes(32, "big")),
            "big",
        )
        slots.append(current)
    return slots


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
    # All costs derived from .gas_cost(fork); no hardcoded constants.

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

    # Derive per-iteration gas from the While loop structure.
    # The real condition uses reserve_gas (unknown yet), but PUSH costs
    # 3 gas regardless of the value, so any placeholder gives the same cost.
    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=keccak_body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    # Exit overhead: condition + jump logic consumed when the loop
    # condition fails (everything except JUMPDEST and body).
    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_keccak_chain_code(reserve_gas)

    # Minimum per-tx gas: intrinsic + setup + one full loop iteration.
    min_per_tx_gas = intrinsic_gas + setup_gas + per_iter_gas

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
    # The real condition uses reserve_gas (unknown yet), but PUSH costs
    # 3 gas regardless of the value, so any placeholder gives the same cost.
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


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "access_pattern",
    [
        pytest.param("sequential", id="sequential"),
        pytest.param("scattered", id="scattered"),
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
def test_prefetch_cold_storage(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
    access_pattern: str,
) -> None:
    """
    Benchmark cold storage prefetching with different access patterns.

    Deploy a contract with pre-populated storage. Each execution
    transaction performs many cold SLOADs via a gas-check loop. The
    ``access_pattern`` parameter controls how slot keys are generated:

    - ``"sequential"``: slots 0, 1, 2, ... (cache-friendly, somewhat
      predictable without a BAL).
    - ``"scattered"``: ``slot = keccak256(prev_slot)`` hash chain
      (each slot depends on computing the previous keccak, so the
      access pattern is unpredictable without a BAL but trivially
      prefetchable with one).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
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

    if access_pattern == "sequential":
        body = Op.POP(
            Op.SLOAD(
                Op.MLOAD(0),
                key_warm=False,
            ),
        ) + Op.MSTORE(
            0,
            Op.ADD(Op.MLOAD(0), 1),
            old_memory_size=32,
            new_memory_size=32,
        )
    else:
        body = Op.MSTORE(
            0,
            Op.SHA3(0, 32, data_size=32),
            old_memory_size=32,
            new_memory_size=32,
        ) + Op.POP(
            Op.SLOAD(
                Op.MLOAD(0),
                key_warm=False,
            ),
        )

    setup_gas = setup.gas_cost(fork)
    body_gas = body.gas_cost(fork)

    # Derive per-iteration gas from the While loop structure.
    # The real condition uses reserve_gas (unknown yet), but PUSH costs
    # 3 gas regardless of the value, so any placeholder gives the same cost.
    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    # Exit overhead: condition + jump logic consumed when the loop
    # condition fails (everything except JUMPDEST and body).
    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    cleanup_gas = Op.STOP.gas_cost(fork)
    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    if access_pattern == "sequential":
        runtime_code = _build_sequential_sload_code(reserve_gas)
    else:
        runtime_code = _build_hash_chain_sload_code(reserve_gas)

    # Minimum per-tx gas: intrinsic + setup + one full loop iteration.
    min_per_tx_gas = intrinsic_gas + setup_gas + per_iter_gas

    num_exec_txs, per_tx_gas = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_count_fraction
    )

    # --- Estimate slots read per tx (for storage pre-population) ---
    available_gas = per_tx_gas - intrinsic_gas - setup_gas
    estimated_slots_per_tx = max(1, available_gas // per_iter_gas)

    # --- Deploy contract with pre-populated storage ---
    #
    # All txs share a single contract. Each tx reads a disjoint range
    # of slots (sequential) or a disjoint hash chain (scattered).
    total_slots = (estimated_slots_per_tx + 1) * num_exec_txs

    chain_seeds: list[int] = []
    storage = Storage()
    if access_pattern == "sequential":
        for i in range(total_slots):
            storage[i] = 1
    else:
        # Pre-compute all hash chains (one per tx) and merge slot keys.
        for tx_idx in range(num_exec_txs):
            seed = tx_idx
            chain = _compute_hash_chain(seed, estimated_slots_per_tx + 1)
            chain_seeds.append(seed)
            for slot_key in chain:
                storage[slot_key] = 1

    contract = pre.deploy_contract(
        code=runtime_code,
        storage=storage,
    )

    # --- Execution block ---
    blocks: list[Block] = []

    with TestPhaseManager.execution():
        exec_txs = []
        for tx_idx in range(num_exec_txs):
            if access_pattern == "sequential":
                start_slot = tx_idx * estimated_slots_per_tx
                calldata = Hash(start_slot)
            else:
                calldata = Hash(chain_seeds[tx_idx])
            exec_txs.append(
                Transaction(
                    to=contract,
                    gas_limit=per_tx_gas,
                    data=calldata,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "value_transfer",
    [
        pytest.param(False, id="implicit_fees"),
        pytest.param(True, id="explicit_coinbase_call"),
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
def test_coinbase_serialization(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
    value_transfer: bool,
) -> None:
    """
    Benchmark coinbase as an implicit serialization point.

    Each tx calls its own contract doing a keccak256 hash chain on a
    private slot.  Storage is completely disjoint across contracts — the
    **only** shared state is the coinbase balance (fee accumulation).

    With ``value_transfer=False`` the dependency is purely implicit
    (protocol-level fee crediting).  With ``value_transfer=True`` each
    contract sends 1 wei to coinbase via ``CALL``, making the
    dependency visible in execution traces and exercising client-specific
    coinbase detection (e.g. Besu's ``TransactionCollisionDetector``).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # --- Gas cost calculation ---
    #
    # Keccak chain costs are the same as test_parallel_execution.
    # The coinbase CALL (when enabled) is an additional fixed cost
    # consumed before the loop.

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
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = keccak_body.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)

    # Derive per-iteration gas from the While loop structure.
    # The real condition uses reserve_gas (unknown yet), but PUSH costs
    # 3 gas regardless of the value, so any placeholder gives the same cost.
    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=keccak_body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    # Exit overhead: condition + jump logic consumed when the loop
    # condition fails (everything except JUMPDEST and body).
    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    # Coinbase CALL gas (only for value_transfer variant).
    # Coinbase is warm per EIP-3651 (Shanghai+).
    coinbase_call_gas = 0
    if value_transfer:
        coinbase_call = Op.POP(
            Op.CALL(
                gas=0,
                address=Op.COINBASE,
                value=1,
                address_warm=True,
                value_transfer=True,
            )
        )
        coinbase_call_gas = coinbase_call.gas_cost(fork)

    if value_transfer:
        runtime_code = _build_keccak_chain_with_coinbase_code(reserve_gas)
    else:
        runtime_code = _build_keccak_chain_code(reserve_gas)

    # Minimum per-tx gas: intrinsic + setup + coinbase call + one iteration.
    min_per_tx_gas = (
        intrinsic_gas + setup_gas + coinbase_call_gas + per_iter_gas
    )

    num_exec_txs, per_tx_gas = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_count_fraction
    )

    # --- Deploy one contract per tx ---
    #
    # Each contract has an independent keccak chain on slot 0.
    # When value_transfer is True, the contract needs 1 wei balance
    # to send to coinbase.
    contracts = []
    for _ in range(num_exec_txs):
        addr = pre.deploy_contract(
            code=runtime_code,
            storage={0: 1},
            balance=1 if value_transfer else 0,
        )
        contracts.append(addr)

    # --- Execution block ---
    blocks: list[Block] = []

    with TestPhaseManager.execution():
        exec_txs = []
        for tx_idx in range(num_exec_txs):
            exec_txs.append(
                Transaction(
                    to=contracts[tx_idx],
                    gas_limit=per_tx_gas,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "pair_independence",
    [
        pytest.param(True, id="independent_pairs"),
        pytest.param(False, id="single_contract"),
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
def test_deploy_then_interact(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
    pair_independence: bool,
) -> None:
    """
    Benchmark structural cross-tx code dependencies.

    Transactions are organized as deploy/call pairs within a single
    block: tx 2k deploys a contract, tx 2k+1 calls it.  Without a BAL,
    clients must discover that the call depends on the deploy through
    speculative execution or re-execution.  With a BAL the dependency
    is explicit.

    With ``pair_independence=True`` each pair deploys and calls its own
    contract — pairs are independent and parallelizable.  With
    ``pair_independence=False`` a single contract is deployed first and
    all subsequent txs call it, creating a fully serial dependency
    chain (deploy + shared slot 0).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # --- Gas cost calculation (keccak chain, same as parallel_execution) ---

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
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = keccak_body.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)

    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=keccak_body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_keccak_chain_code(reserve_gas)

    # --- Deploy gas estimation ---
    #
    # Each deploy tx creates a keccak chain contract with SSTORE(0, 1)
    # as initcode prefix.  Cost = intrinsic (create tx) + initcode
    # execution + code deposit.
    creation_code = Initcode(
        deploy_code=runtime_code,
        initcode_prefix=Op.SSTORE(0, 1),
    )

    intrinsic_gas_create = intrinsic_gas_calculator(
        calldata=bytes(creation_code),
        contract_creation=True,
    )

    initcode_sstore = Op.SSTORE(
        0,
        1,
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    initcode_exec_gas = initcode_sstore.gas_cost(fork)
    code_deposit_gas = 200 * len(runtime_code)

    # Buffer covers Initcode wrapper (CODECOPY + RETURN + memory).
    deploy_gas_limit = (
        intrinsic_gas_create + initcode_exec_gas + code_deposit_gas + 10000
    )

    # --- Tx count and gas allocation ---

    min_call_gas = intrinsic_gas + setup_gas + per_iter_gas

    if pair_independence:
        # N pairs: [deploy_0, call_0, deploy_1, call_1, ...]
        min_per_pair = deploy_gas_limit + min_call_gas
        max_pairs = gas_benchmark_value // min_per_pair
        if tx_count_fraction == 0.0:
            num_pairs = 1
        else:
            num_pairs = max(1, int(max_pairs * tx_count_fraction))
        per_pair_gas = gas_benchmark_value // num_pairs
        call_gas_limit = min(tx_gas_limit, per_pair_gas - deploy_gas_limit)
        num_call_txs = num_pairs
    else:
        # 1 deploy + N calls: [deploy_0, call_0, call_1, ...]
        call_budget = gas_benchmark_value - deploy_gas_limit
        max_calls = call_budget // min_call_gas
        if tx_count_fraction == 0.0:
            num_call_txs = 1
        else:
            num_call_txs = max(1, int(max_calls * tx_count_fraction))
        call_gas_limit = min(tx_gas_limit, call_budget // num_call_txs)
        num_pairs = 1

    # --- Build block ---

    blocks: list[Block] = []

    with TestPhaseManager.execution():
        exec_txs: list[Transaction] = []

        if pair_independence:
            # Interleaved deploy/call pairs.
            for _ in range(num_pairs):
                deployer = pre.fund_eoa()
                exec_txs.append(
                    Transaction(
                        to=None,
                        gas_limit=deploy_gas_limit,
                        data=creation_code,
                        sender=deployer,
                    )
                )
                contract = compute_create_address(address=deployer, nonce=0)
                exec_txs.append(
                    Transaction(
                        to=contract,
                        gas_limit=call_gas_limit,
                        sender=pre.fund_eoa(),
                    )
                )
        else:
            # Single deploy followed by serial calls.
            deployer = pre.fund_eoa()
            exec_txs.append(
                Transaction(
                    to=None,
                    gas_limit=deploy_gas_limit,
                    data=creation_code,
                    sender=deployer,
                )
            )
            contract = compute_create_address(address=deployer, nonce=0)
            for _ in range(num_call_txs):
                exec_txs.append(
                    Transaction(
                        to=contract,
                        gas_limit=call_gas_limit,
                        sender=pre.fund_eoa(),
                    )
                )

        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "group_size",
    [
        pytest.param(1, id="group_size_1"),
        pytest.param(2, id="group_size_2"),
        pytest.param(5, id="group_size_5"),
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
def test_mixed_dependency_graph(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_count_fraction: float,
    group_size: int,
) -> None:
    """
    Benchmark partial-order parallel scheduling.

    K independent groups each form an internally serial keccak chain
    (shared slot 0).  Groups are **interleaved** in the block::

        [g0_tx0, g1_tx0, g2_tx0, g0_tx1, g1_tx1, g2_tx1, ...]

    This prevents position-based heuristics from discovering parallelism
    without analyzing state dependencies.

    ``group_size=1`` is fully parallel (degenerate baseline).
    ``group_size=5`` creates long serial chains with limited parallelism.
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # --- Gas cost calculation (same keccak chain as parallel_execution) ---

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
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    body_gas = keccak_body.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)

    placeholder_condition = Op.GT(Op.GAS, 0)
    placeholder_loop = While(body=keccak_body, condition=placeholder_condition)
    per_iter_gas = placeholder_loop.gas_cost(fork)

    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)

    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_keccak_chain_code(reserve_gas)

    min_per_tx_gas = intrinsic_gas + setup_gas + per_iter_gas

    num_exec_txs, per_tx_gas = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_count_fraction
    )

    # Round down to complete groups.
    num_groups = max(1, num_exec_txs // group_size)
    num_exec_txs = num_groups * group_size

    # --- Deploy one contract per group (setup block) ---
    creation_code = Initcode(
        deploy_code=runtime_code,
        initcode_prefix=Op.SSTORE(0, 1),
    )

    blocks = []

    with TestPhaseManager.setup():
        deploy_txs = []
        deployers = []
        for _ in range(num_groups):
            deployer = pre.fund_eoa()
            deployers.append(deployer)
            deploy_txs.append(
                Transaction(
                    to=None,
                    gas_limit=tx_gas_limit,
                    data=creation_code,
                    sender=deployer,
                )
            )
        blocks.append(Block(txs=deploy_txs))

    group_contracts = [
        compute_create_address(address=d, nonce=0) for d in deployers
    ]

    # --- Execution block: interleaved round-robin ---
    with TestPhaseManager.execution():
        exec_txs = []
        for _round_idx in range(group_size):
            for group_idx in range(num_groups):
                exec_txs.append(
                    Transaction(
                        to=group_contracts[group_idx],
                        gas_limit=per_tx_gas,
                        sender=pre.fund_eoa(),
                    )
                )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)
