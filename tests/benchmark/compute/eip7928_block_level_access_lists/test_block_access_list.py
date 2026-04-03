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
from enum import Enum, auto

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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7928.md"
REFERENCE_SPEC_VERSION = "aca88aa0932580c29d0233f902cb4390e88b8c41"

pytestmark = pytest.mark.valid_from("Amsterdam")

# Sentinel slot for inter-tx serialization in prefetch tests.
# Chosen as max uint256 to avoid collision with data slots.
_POINTER_SLOT = 2**256 - 1


class TxDensity(Enum):
    """
    Control how many transactions a gas budget is divided into.

    GREEDY: pack ``tx_gas_limit``-sized transactions (fewest txs).
    HALF: 50 % of the maximum possible transaction count.
    MAX: maximum transaction count (each tx at minimum viable gas).
    """

    GREEDY = auto()
    HALF = auto()
    MAX = auto()


def _derive_loop_gas(body: Bytecode, fork: Fork) -> tuple[int, int]:
    """
    Derive per-iteration gas and exit overhead for a While loop.

    Return ``(per_iter_gas, exit_overhead)``.

    Uses a placeholder condition (``GT(GAS, 0)``) to measure the loop
    overhead.  ``PUSH`` costs 3 gas regardless of the pushed value if
    the value is nonzero, so the real condition (which pushes ``reserve_gas``)
    has the same cost.
    """
    body_gas = body.gas_cost(fork)
    placeholder = Op.GT(Op.GAS, Op.PUSH1(0))
    per_iter_gas = While(body=body, condition=placeholder).gas_cost(fork)
    exit_overhead = per_iter_gas - body_gas - Op.JUMPDEST.gas_cost(fork)
    return per_iter_gas, exit_overhead


def _build_keccak_chain(
    fork: Fork,
) -> tuple[Bytecode, int, int, int]:
    """
    Build keccak chain code and compute gas schedule.

    Return ``(code, setup_gas, per_iter_gas, reserve_gas)``.

    Contract flow:

    1. Store literal ``1`` as seed in memory (no state access).
    2. Keccak loop: ``MSTORE(0, SHA3(0, 32))`` until gas reserve.
    3. Cleanup: ``SSTORE(0, ADD(SLOAD(0), MLOAD(0)))`` then STOP.

    SLOAD(0) is deliberately placed in cleanup so speculative
    parallel execution wastes maximum resources before discovering
    the shared-state conflict on slot 0.
    """
    prefix = Op.MSTORE(
        0,
        1,
        old_memory_size=0,
        new_memory_size=32,
    )

    keccak_body = Op.MSTORE(
        0,
        Op.SHA3(0, 32, data_size=32),
        old_memory_size=32,
        new_memory_size=32,
    )

    # Cleanup: combine loop result with shared state, then store.
    # SLOAD(0) is the first state access — deliberately late to
    # force speculative parallel execution to waste maximum
    # resources before discovering the shared-state conflict.
    cleanup = (
        Op.SSTORE(
            0,
            Op.ADD(
                Op.SLOAD(0, key_warm=False),
                Op.MLOAD(0),
            ),
            key_warm=True,
            # Placeholder: actual value differs per tx but gas cost
            # is identical for any nonzero -> nonzero write.
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = prefix.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)
    per_iter_gas, exit_overhead = _derive_loop_gas(keccak_body, fork)
    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    condition = Op.GT(Op.GAS, reserve_gas)
    loop = While(body=keccak_body, condition=condition)

    return prefix + loop + cleanup, setup_gas, per_iter_gas, reserve_gas


def _build_sequential_sstore_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code that SSTOREs to sequential cold storage slots.

    Read ``start_slot`` from ``calldata[0:32]``, then loop writing a
    max-weight value (``2**256 - 1``) to ``slot``, ``slot - 1``, ...
    until remaining gas drops below ``reserve_gas``.  Counting down
    from high keys with 32-byte values maximizes RLP encoding weight
    per trie leaf for state root computation benchmarks.

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
        2**256 - 1,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2**256 - 1,
    ) + Op.MSTORE(
        0,
        Op.SUB(Op.MLOAD(0), 1),
        old_memory_size=32,
        new_memory_size=32,
    )

    condition = Op.GT(Op.GAS, reserve_gas)

    loop = While(body=sstore_body, condition=condition)

    return setup + loop + Op.STOP


def _build_sload_chain_code(reserve_gas: int) -> Bytecode:
    """
    Build runtime code that SLOADs a linked-list chain.

    Read seed from ``_POINTER_SLOT``, then loop:
    ``next_key = SLOAD(key)`` — the stored value IS the next key.
    Repeat until remaining gas drops below ``reserve_gas``.  Write
    final key back to ``_POINTER_SLOT`` to serialize transactions.

    Keys are unpredictable without reading storage, so clients can
    only prefetch via the BAL.

    Caller must initialize ``_POINTER_SLOT`` to a nonzero value so
    the final SSTORE is a nonzero-to-nonzero write for gas costing.

    Memory layout: ``[0:32]`` = current slot key.
    """
    setup = Op.MSTORE(
        0,
        Op.SLOAD(_POINTER_SLOT, key_warm=False),
        old_memory_size=0,
        new_memory_size=32,
    )

    sload_body = Op.MSTORE(
        0,
        Op.SLOAD(
            Op.MLOAD(0),
            key_warm=False,
        ),
        old_memory_size=32,
        new_memory_size=32,
    )

    condition = Op.GT(Op.GAS, reserve_gas)
    loop = While(body=sload_body, condition=condition)

    cleanup = (
        Op.SSTORE(
            _POINTER_SLOT,
            Op.MLOAD(0),
            key_warm=True,
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    return setup + loop + cleanup


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
    tx_density: TxDensity,
) -> list[int]:
    """
    Derive a list of per-tx gas limits that fill the gas budget.

    ``GREEDY``: pack as many ``tx_gas_limit``-sized transactions as
    fit and append a smaller remainder if the leftover gas meets
    ``min_per_tx_gas``.

    ``HALF``: use 50 % of the maximum possible transaction count and
    distribute gas equally.

    ``MAX``: maximize the transaction count (each tx near
    ``min_per_tx_gas``).
    """
    if tx_density is TxDensity.GREEDY:
        num_full = gas_benchmark_value // tx_gas_limit
        remainder = gas_benchmark_value - num_full * tx_gas_limit
        schedule = [tx_gas_limit] * num_full
        if remainder >= min_per_tx_gas:
            schedule.append(remainder)
        return schedule

    max_num_txs = gas_benchmark_value // min_per_tx_gas
    fraction = 0.5 if tx_density is TxDensity.HALF else 1.0
    num_txs = max(1, int(max_num_txs * fraction))
    per_tx_gas = max(
        min_per_tx_gas,
        min(tx_gas_limit, gas_benchmark_value // num_txs),
    )
    return [per_tx_gas] * num_txs


TX_DENSITY_PARAMS = [
    pytest.param(TxDensity.GREEDY, id="greedy_fill"),
    pytest.param(TxDensity.HALF, id="half_max_txs"),
    pytest.param(TxDensity.MAX, id="max_txs"),
]


def test_parallel_execution_serial_chain(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark a fully serial chain as a baseline for parallel execution.

    All transactions conflict on slot 0 — with a BAL, clients know
    upfront the block is serial and avoid speculation overhead.

    Deploy a contract that initializes storage slot 0 to 1. Each
    execution transaction performs a keccak256 hash chain from a
    literal ``1`` seed (iteration count determined by available gas),
    then combines the result with slot 0 via
    ``SSTORE(0, ADD(SLOAD(0), result))``.

    The shared-state access (SLOAD/SSTORE on slot 0) is
    deliberately placed at the end so speculative parallel
    execution wastes maximum resources before discovering the
    conflict.
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    runtime_code, setup_gas, _, reserve_gas = _build_keccak_chain(fork)
    min_per_tx_gas = intrinsic_gas + setup_gas + reserve_gas

    tx_gas_schedule = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, TxDensity.GREEDY
    )

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
        for gas_limit in tx_gas_schedule:
            exec_txs.append(
                Transaction(
                    to=contract_address,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.parametrize(
    "contract_per_tx",
    [
        pytest.param(False, id="single_contract"),
        pytest.param(True, id="contract_per_tx"),
    ],
)
@pytest.mark.parametrize("tx_density", TX_DENSITY_PARAMS)
def test_state_root_computation(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_density: TxDensity,
    contract_per_tx: bool,
) -> None:
    """
    Benchmark state root computation with disjoint storage writes.

    Deploy contracts with pre-populated storage. Each execution
    transaction writes to a non-overlapping range of sequential cold
    storage slots via a gas-check loop, so all transactions are
    genuinely independent.

    The ``contract_per_tx`` parameter controls whether each
    transaction targets a unique contract (maximizing account trie
    width) or all transactions share a single contract (maximizing
    storage trie depth).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    # Worst-case calldata: 32 nonzero bytes for start_slot.
    intrinsic_gas = intrinsic_gas_calculator(calldata=b"\xff" * 32)

    # Reconstruct body bytecode to extract gas components;
    # _build_sequential_sstore_code only returns assembled code.
    setup = Op.MSTORE(
        0,
        Op.CALLDATALOAD(0),
        old_memory_size=0,
        new_memory_size=32,
    )

    sstore_body = Op.SSTORE(
        Op.MLOAD(0),
        2**256 - 1,
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2**256 - 1,
    ) + Op.MSTORE(
        0,
        Op.SUB(Op.MLOAD(0), 1),
        old_memory_size=32,
        new_memory_size=32,
    )

    setup_gas = setup.gas_cost(fork)
    per_iter_gas, exit_overhead = _derive_loop_gas(sstore_body, fork)
    cleanup_gas = Op.STOP.gas_cost(fork)
    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_sequential_sstore_code(reserve_gas)
    min_per_tx_gas = intrinsic_gas + setup_gas + reserve_gas

    tx_gas_schedule = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_density
    )
    num_exec_txs = len(tx_gas_schedule)

    available_gas = tx_gas_schedule[0] - intrinsic_gas - setup_gas
    estimated_slots_per_tx = max(1, available_gas // per_iter_gas)

    num_contracts = num_exec_txs if contract_per_tx else 1
    txs_per_contract = math.ceil(num_exec_txs / num_contracts)
    slots_per_contract = (estimated_slots_per_tx + 1) * txs_per_contract

    # Pre-populate storage counting down from near-max uint256.
    # High slot keys + 32-byte stored values maximize RLP weight
    # per trie leaf for state root computation.
    high_start = 2**256 - 1
    contracts = []
    for _ in range(num_contracts):
        storage: Storage.StorageDictType = {
            high_start - i: 1 for i in range(slots_per_contract)
        }
        addr = pre.deploy_contract(
            code=runtime_code,
            storage=storage,
        )
        contracts.append(addr)

    blocks: list[Block] = []
    contract_tx_counts = [0] * num_contracts

    with TestPhaseManager.execution():
        exec_txs = []
        for tx_idx in range(num_exec_txs):
            c_idx = tx_idx % num_contracts
            start_slot = (
                high_start - contract_tx_counts[c_idx] * estimated_slots_per_tx
            )
            contract_tx_counts[c_idx] += 1
            exec_txs.append(
                Transaction(
                    to=contracts[c_idx],
                    gas_limit=tx_gas_schedule[tx_idx],
                    data=Hash(start_slot),
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


def test_prefetch_cold_storage(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark cold storage prefetching via an SLOAD linked-list chain.

    Deploy a contract with pre-populated linked-list storage where
    each slot's value is the next key.  Each execution transaction
    performs back-to-back cold SLOADs with minimal compute between reads
    — a worst-case prefetch scenario.

    Keys are unpredictable without reading storage, so clients can
    only prefetch via the BAL.

    A shared pointer slot (``_POINTER_SLOT``) serializes
    transactions: each tx reads its seed from the pointer and writes
    back the final key, preventing parallel execution without a BAL.

    The BAL makes all accessed slots prefetchable: the data slots
    appear in ``storage_reads`` (SLOADs not also written per
    EIP-7928), while ``_POINTER_SLOT`` appears in
    ``storage_changes`` (both read and written).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    # Reconstruct body bytecode to extract gas components;
    # _build_sload_chain_code only returns assembled code.
    setup = Op.MSTORE(
        0,
        Op.SLOAD(_POINTER_SLOT, key_warm=False),
        old_memory_size=0,
        new_memory_size=32,
    )

    body = Op.MSTORE(
        0,
        Op.SLOAD(
            Op.MLOAD(0),
            key_warm=False,
        ),
        old_memory_size=32,
        new_memory_size=32,
    )

    cleanup = (
        Op.SSTORE(
            _POINTER_SLOT,
            Op.MLOAD(0),
            key_warm=True,
            original_value=1,
            current_value=1,
            new_value=2,
        )
        + Op.STOP
    )

    setup_gas = setup.gas_cost(fork)
    cleanup_gas = cleanup.gas_cost(fork)
    per_iter_gas, exit_overhead = _derive_loop_gas(body, fork)
    reserve_gas = per_iter_gas + exit_overhead + cleanup_gas

    runtime_code = _build_sload_chain_code(reserve_gas)

    min_per_tx_gas = intrinsic_gas + setup_gas + reserve_gas

    tx_gas_schedule = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, TxDensity.GREEDY
    )
    num_exec_txs = len(tx_gas_schedule)

    available_gas = tx_gas_schedule[0] - intrinsic_gas - setup_gas
    estimated_slots_per_tx = max(1, available_gas // per_iter_gas)

    # All txs share a single contract with disjoint slot ranges.
    total_slots = (estimated_slots_per_tx + 1) * num_exec_txs

    # Build linked-list storage: each tx continues where the
    # previous left off via the shared pointer slot.
    chain = _compute_hash_chain(1, total_slots)
    storage = Storage()
    storage[1] = chain[0]
    for i in range(len(chain) - 1):
        storage[chain[i]] = chain[i + 1]
    storage[chain[-1]] = chain[-1]

    # Nonzero initial value keeps the cleanup SSTORE a
    # nonzero -> nonzero write (cheaper than 0 -> nonzero).
    storage[_POINTER_SLOT] = 1

    contract = pre.deploy_contract(
        code=runtime_code,
        storage=storage,
    )

    blocks: list[Block] = []

    with TestPhaseManager.execution():
        exec_txs = []
        for gas_limit in tx_gas_schedule:
            exec_txs.append(
                Transaction(
                    to=contract,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                )
            )
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.parametrize(
    "pair_independence",
    [
        pytest.param(True, id="independent_pairs"),
        pytest.param(False, id="single_contract"),
    ],
)
@pytest.mark.parametrize("tx_density", TX_DENSITY_PARAMS)
def test_deploy_then_interact(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_density: TxDensity,
    pair_independence: bool,
) -> None:
    """
    Benchmark structural cross-tx code dependencies.

    Transactions include deploy and call operations within a single
    block.  Without a BAL, clients must discover that calls depend on
    deploys through speculative execution or re-execution.  With a BAL
    the dependency is explicit.

    With ``pair_independence=True`` each pair deploys and calls its own
    contract — pairs are independent and parallelizable.  With
    ``pair_independence=False`` a single contract is deployed first and
    all subsequent txs call it, creating a fully serial dependency
    chain (deploy + shared slot 0).
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()

    runtime_code, setup_gas, _, reserve_gas = _build_keccak_chain(fork)

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

    # Buffer for Initcode wrapper overhead (CODECOPY + RETURN + memory).
    deploy_gas_limit = (
        intrinsic_gas_create + initcode_exec_gas + code_deposit_gas + 10000
    )

    min_call_gas = intrinsic_gas + setup_gas + reserve_gas

    fraction = {
        TxDensity.GREEDY: None,
        TxDensity.HALF: 0.5,
        TxDensity.MAX: 1.0,
    }[tx_density]

    if pair_independence:
        # N pairs: [deploy_0, call_0, deploy_1, call_1, ...]
        if fraction is None:
            per_pair_gas = deploy_gas_limit + tx_gas_limit
            num_pairs = max(1, gas_benchmark_value // per_pair_gas)
            remainder = gas_benchmark_value - num_pairs * per_pair_gas
            if remainder >= deploy_gas_limit + min_call_gas:
                num_pairs += 1
        else:
            min_per_pair = deploy_gas_limit + min_call_gas
            max_pairs = gas_benchmark_value // min_per_pair
            num_pairs = max(1, int(max_pairs * fraction))
        per_pair_gas = gas_benchmark_value // num_pairs
        call_gas_limit = min(tx_gas_limit, per_pair_gas - deploy_gas_limit)
        num_call_txs = num_pairs
    else:
        # 1 deploy + N calls: [deploy_0, call_0, call_1, ...]
        call_budget = gas_benchmark_value - deploy_gas_limit
        if fraction is None:
            num_call_txs = call_budget // tx_gas_limit
            remainder = call_budget - num_call_txs * tx_gas_limit
            if remainder >= min_call_gas:
                num_call_txs += 1
        else:
            max_calls = call_budget // min_call_gas
            num_call_txs = max(1, int(max_calls * fraction))
        call_gas_limit = min(tx_gas_limit, call_budget // num_call_txs)
        num_pairs = 1

    blocks: list[Block] = []

    with TestPhaseManager.execution():
        exec_txs: list[Transaction] = []

        if pair_independence:
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


@pytest.mark.parametrize(
    "group_size",
    [
        pytest.param(1, id="group_size_1"),
        pytest.param(2, id="group_size_2"),
        pytest.param(5, id="group_size_5"),
    ],
)
@pytest.mark.parametrize("tx_density", TX_DENSITY_PARAMS)
def test_mixed_dependency_graph(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    tx_density: TxDensity,
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

    runtime_code, setup_gas, _, reserve_gas = _build_keccak_chain(fork)
    min_per_tx_gas = intrinsic_gas + setup_gas + reserve_gas

    tx_gas_schedule = _derive_tx_schedule(
        gas_benchmark_value, min_per_tx_gas, tx_gas_limit, tx_density
    )

    # Round down to complete groups; skip if the gas budget cannot
    # fill even one complete group.
    total_txs = len(tx_gas_schedule)
    num_groups = total_txs // group_size
    if num_groups == 0:
        pytest.skip(
            f"Gas budget too low for group_size={group_size} "
            f"(only {total_txs} txs fit)"
        )
    num_exec_txs = num_groups * group_size
    tx_gas_schedule = tx_gas_schedule[:num_exec_txs]

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

    # Interleaved round-robin: txs from different groups alternate.
    with TestPhaseManager.execution():
        exec_txs = []
        tx_idx = 0
        for _round_idx in range(group_size):
            for group_idx in range(num_groups):
                exec_txs.append(
                    Transaction(
                        to=group_contracts[group_idx],
                        gas_limit=tx_gas_schedule[tx_idx],
                        sender=pre.fund_eoa(),
                    )
                )
                tx_idx += 1
        blocks.append(Block(txs=exec_txs))

    benchmark_test(blocks=blocks, skip_gas_used_validation=True)
