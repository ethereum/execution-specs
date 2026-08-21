"""Benchmark SLOAD operations on bloated and delegated storage."""

from functools import partial
from typing import Generator

import pytest
from execution_testing import (
    EOA,
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
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    RecipientType,
    Storage,
    TestPhaseManager,
    Transaction,
    While,
)

from tests.benchmark.helper.delegation import (
    build_delegated_storage_setup,
    delegate_with_calldata,
    run_bloated_eoa_benchmark,
)
from tests.benchmark.helper.enums import CacheStrategy
from tests.benchmark.helper.storage import (
    START_SLOT,
    access_list_generator,
    create_sstore_initializer,
    executor_calldata_generator,
    initializer_calldata_generator,
)

LOOP_GAS_THRESHOLD = 0xFFFF


def _max_sloads_per_tx(tx_gas_limit: int, fork: Fork) -> int:
    """
    Conservative upper bound on cold SLOADs that fit in a max-gas tx.

    Derived from the fork's cold `SLOAD` cost (`COLD_STORAGE_ACCESS`)
    and used by the bloated SLOAD benchmarks both as the inter-tx
    offset stride (to keep consecutive txs' SLOAD ranges disjoint) and
    as the per-target storage pre-load count.
    """
    cold_sload_cost = Op.SLOAD(key_warm=False).gas_cost(fork)
    return tx_gas_limit // cold_sload_cost


def _sender_generator(
    pre: Alloc, distinct_senders: bool
) -> Generator[EOA, None, None]:
    """
    Yield one sender per tx.

    In distinct mode, yields a fresh EOA per call. Otherwise, yields
    the same shared sender for every call. Used by the bloated SLOAD
    benchmarks so the BAL builder can group nonce changes by sender
    uniformly regardless of mode.
    """
    shared_sender = pre.fund_eoa() if not distinct_senders else None
    while True:
        yield pre.fund_eoa() if shared_sender is None else shared_sender


def create_sload_executor(key_warm: bool) -> IteratingBytecode:
    """
    Create a contract that executes SLOAD benchmark operations.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)

    Returns: IteratingBytecode representing the benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST
    # Loop Body: Load from current slot
    loop += Op.DUP1  # [counter, counter, end_slot]
    loop += Op.SLOAD(key_warm=key_warm)
    loop += Op.POP  # [counter, end_slot]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, end_slot]

    # Loop Condition: Counter < end_slot
    loop += Op.DUP2  # [end_slot, counter + 1, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, end_slot]
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, end_slot]

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize("storage_keys_pre_set", [True, False])
def test_sload_benchmark(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    storage_keys_pre_set: bool,
) -> None:
    """
    Benchmark SLOAD instruction with various configurations.

    Uses EIP-7702 delegation. The authority EOA delegates to:

    - StorageInitializer: storage[i] = 1 (if storage_keys_pre_set)
    - BenchmarkExecutor: performs the benchmark operation (SLOAD)

    Variants:

    - access_warm: Warm storage slots via access list
    - storage_keys_pre_set: Whether the storage keys are pre-set
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(init_val=1)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Actual Benchmark Execution
    executor_code = create_sload_executor(key_warm=access_warm)
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(executor_calldata_generator)
    access_list_gen = partial(
        access_list_generator, access_warm=access_warm, authority=authority
    )

    # Number of slots that can be processed in the execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata_gen,
            access_list=access_list_gen,
            start_iteration=1,
            recipient_type=RecipientType.DELEGATION_7702,
        )
    )

    # Setup phase: initialize storage slots (if storage_keys_pre_set)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            block_gas_budget=gas_benchmark_value,
            needs_init=storage_keys_pre_set,
            num_target_slots=num_target_slots,
            initializer_code=initializer_code,
            initializer_addr=initializer_addr,
            executor_addr=executor_addr,
            authority=authority,
            authority_nonce=authority_nonce,
            delegation_sender=delegation_sender,
            initializer_calldata_generator=initializer_calldata_generator,
        )

    # Execution phase
    expected_gas_used = 0

    with TestPhaseManager.execution():
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=calldata_gen,
                start_iteration=1,
                access_list=access_list_gen,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

        expected_gas_used = sum(tx.gas_cost for tx in exec_txs)

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


@pytest.mark.repricing
@pytest.mark.parametrize("storage_keys_pre_set", [False, True])
def test_sload_same_key_benchmark(
    benchmark_test: BenchmarkTestFiller,
    storage_keys_pre_set: bool,
) -> None:
    """
    Benchmark SLOAD instruction when loading the same key over and over.

    Variants:

    - storage_keys_pre_set: The key is pre-set to a non-zero value.
    """
    contract_storage = Storage()
    if storage_keys_pre_set:
        contract_storage[1] = 1

    benchmark_test(
        target_opcode=Op.SLOAD,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH1(1) if storage_keys_pre_set else Op.PUSH0,
            attack_block=Op.SLOAD,
            contract_storage=contract_storage,
        ),
    )


@pytest.mark.repricing
@pytest.mark.stub_parametrize("token_name", "bloated_eoa_")
@pytest.mark.parametrize("existing_slots", [False, True])
@pytest.mark.parametrize("cache_strategy", [CacheStrategy.NO_CACHE])
def test_sload_bloated(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    existing_slots: bool,
    cache_strategy: CacheStrategy,
) -> None:
    """
    Benchmark SLOAD opcodes targeting an EOA with storage bloated.

    The storage is assumed to be filled from 0-N linearly, where
    each slot has the value of the key. If this is not the
    storage layout of the target account, then the existing_slots
    parameter will not be correct.
    """
    slot_access = (
        Op.DUP1  # [index, index]
        + Op.SLOAD  # [s[index], index]
        + Op.POP  # [index]
    )
    # CACHE_TX: access each slot twice so the second hit is uncached
    if cache_strategy == CacheStrategy.CACHE_TX:
        slot_access *= 2

    runtime_code = (
        Op.PUSH0  # [0]
        + Op.SLOAD  # [index], s[0] = index
        + While(
            body=(
                slot_access
                + Op.PUSH1(1)  # [1, index]
                + Op.ADD  # [index+1]
            ),
            condition=Op.GT(Op.GAS, LOOP_GAS_THRESHOLD),
        )
        + Op.PUSH0  # [0, index+1]
        + Op.SSTORE  # s[0] = index+1
    )

    run_bloated_eoa_benchmark(
        benchmark_test=benchmark_test,
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        authority=pre.stub_eoa(token_name),
        existing_slots=existing_slots,
        runtime_code=runtime_code,
        cache_strategy=cache_strategy,
    )


@pytest.mark.stub_parametrize("token_name", "bloated_eoa_")
@pytest.mark.parametrize("distinct_senders", [False, True])
@pytest.mark.parametrize("existing_slots", [False, True])
def test_sload_bloated_prefetch_miss(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    existing_slots: bool,
    distinct_senders: bool,
) -> None:
    """
    Benchmark SLOAD with calldata-driven offsets to defeat prefetching.

    A small first transaction writes an initial offset into the
    authority's slot 0 via calldata. Subsequent max-gas transactions
    each read the previous offset from slot 0, immediately overwrite
    slot 0 with a new offset from their own calldata, then SLOAD
    sequentially from the previous offset. Because each transaction's
    SLOAD range depends on state written by its predecessor, a
    prefetcher that predicts SLOAD targets from pre-block state
    without simulating intra-block writes will pre-warm incorrect
    storage slots. The minimal first tx is load-bearing: it lives
    inside the benchmark block so every subsequent max-gas tx reads
    a slot 0 value that differs from the prefetcher's pre-block
    snapshot, achieving a 100% miss rate.

    When ``distinct_senders`` is True every transaction uses a fresh
    sender. This additionally defeats per-sender prewarm
    serialization (e.g. Nethermind) that groups txs by sender and
    runs them sequentially to propagate state changes — forcing
    every tx's prewarm scope to restart from pre-block state.
    """
    plant_code = Op.SLOAD(Op.PUSH0, key_warm=False) + Op.SSTORE(
        Op.PUSH0,
        Op.CALLDATALOAD(Op.PUSH0),
        key_warm=True,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    # Read the old offset from slot 0, write the new offset from
    # calldata to slot 0, then SLOAD sequentially from the old offset.
    runtime_code = plant_code + While(
        body=(Op.DUP1 + Op.SLOAD + Op.POP + Op.PUSH1(1) + Op.ADD),
        condition=Op.GT(Op.GAS, LOOP_GAS_THRESHOLD),
    )

    authority = pre.stub_eoa(token_name)
    runtime_address = pre.deploy_contract(code=runtime_code)

    # Setup: delegate authority to the runtime contract. Slot 0 is
    # left at 0 (the delegation tx's calldata) so the benchmark
    # block's pre-state has slot 0 = 0; the first benchmark tx
    # then plants base_offset in slot 0 inside the benchmark block,
    # forcing the prefetcher's pre-block snapshot to disagree with
    # the actual slot 0 value seen by every max-gas tx that follows.
    delegation_tx = delegate_with_calldata(
        pre,
        fork,
        authority,
        runtime_address,
        Hash(0),
    )

    blocks: list[Block] = [Block(txs=[delegation_tx])]

    # Offset spacing: upper bound on SLOADs per tx ensures each
    # transaction reads a completely disjoint slot range.
    max_sloads_per_tx = _max_sloads_per_tx(tx_gas_limit, fork)

    # The base offset must be at least max_sloads_per_tx away from
    # the pre-block slot 0 value (0) so the prefetcher's predicted
    # SLOAD range is completely disjoint from the actual range.
    base_offset = max_sloads_per_tx if existing_slots else START_SLOT
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32,
        recipient_type=RecipientType.DELEGATION_7702,
    ) + fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.DELEGATION_7702
    )

    plant_tx_gas = (
        intrinsic_gas + plant_code.gas_cost(fork) + LOOP_GAS_THRESHOLD
    )

    # senders_iter yields one sender per tx (fresh per call in
    # distinct mode, a single shared sender otherwise). The senders
    # list collects one entry per tx so the BAL builder below can
    # group nonce changes by sender uniformly.
    senders_iter = _sender_generator(pre, distinct_senders)
    senders: list[EOA] = []

    gas_available = gas_benchmark_value
    txs: list[Transaction] = []

    # This tx's job is to change slot 0 inside the benchmark block so
    # every subsequent max-gas tx reads an offset the prefetcher's
    # pre-block snapshot does not see, achieving a 100% miss rate.
    first_tx_gas = min(gas_available, plant_tx_gas)
    sender = next(senders_iter)
    senders.append(sender)
    txs.append(
        Transaction(
            gas_limit=first_tx_gas,
            to=authority,
            data=Hash(base_offset),
            sender=sender,
        )
    )
    gas_available -= first_tx_gas

    # Subsequent transactions: max gas, each shifts the offset
    # so the next transaction SLOADs from a different range.
    tx_index = 1
    while gas_available >= plant_tx_gas:
        tx_gas = min(gas_available, tx_gas_limit)
        new_offset = base_offset + tx_index * max_sloads_per_tx
        sender = next(senders_iter)
        senders.append(sender)
        txs.append(
            Transaction(
                gas_limit=tx_gas,
                to=authority,
                data=Hash(new_offset),
                sender=sender,
            )
        )
        gas_available -= tx_gas
        tx_index += 1

    expectations: dict[Address, BalAccountExpectation] = {
        authority: BalAccountExpectation(
            storage_reads=[base_offset],
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    validate_any_change=True,
                ),
            ],
        ),
    }
    sender_nonces: dict[Address, list[BalNonceChange]] = {}
    for i, s in enumerate(senders):
        changes = sender_nonces.setdefault(s, [])
        changes.append(
            BalNonceChange(
                block_access_index=i + 1,
                post_nonce=len(changes) + 1,
            )
        )
    for addr, nonces in sender_nonces.items():
        expectations[addr] = BalAccountExpectation(nonce_changes=nonces)
    blocks.append(
        Block(
            txs=txs,
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations=expectations,
            ),
        )
    )

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )


@pytest.mark.parametrize("distinct_senders", [False, True])
@pytest.mark.parametrize("existing_slots", [False, True])
def test_sload_bloated_multi_contract(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    existing_slots: bool,
    distinct_senders: bool,
) -> None:
    """
    Benchmark SLOAD across a distinct contract per transaction.

    Each transaction calls a freshly-deployed contract whose slot 0
    is pre-loaded with the starting offset; the contract then runs a
    SLOAD loop over sequential slots until gas runs low. Unlike
    test_sload_bloated_prefetch_miss which hammers one account's
    storage trie via an EIP-7702 delegated EOA, every transaction
    here opens a different storage trie, stressing cross-account
    state access and state-trie breadth in a single block.

    Every target contract first CALLs a shared offset_holder
    contract whose slot 0 is read, incremented, and written back.
    This mirrors the first test's "same-contract slot 0" dependency
    pattern via cross-contract CALL: every transaction forms a
    read-after-write edge on offset_holder's slot 0, preventing
    parallel execution.

    When ``distinct_senders`` is True every transaction uses a fresh
    sender. This additionally exercises per-sender prewarm
    serialization (e.g. Nethermind) differently than the shared-
    sender case; we run both so clients can be measured in both
    regimes.
    """
    # Shared offset_holder: reads, increments, and writes its own
    # slot 0. Every target CALLs this to create an inter-tx RAW
    # dependency chain on a single shared storage slot.
    offset_holder = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)),
    )

    # Target runtime: CALL offset_holder (for the dependency), then
    # run the same SLOAD loop as test_sload_bloated in its own
    # storage. Final counter is written back to slot 0.
    runtime_code = (
        Op.POP(
            Op.CALL(
                address=offset_holder,
            )
        )
        + Op.SLOAD(Op.PUSH0)
        + While(
            body=(Op.DUP1 + Op.SLOAD + Op.POP + Op.PUSH1(1) + Op.ADD),
            condition=Op.GT(Op.GAS, LOOP_GAS_THRESHOLD),
        )
        + Op.PUSH0
        + Op.SSTORE
    )

    base_offset = 1 if existing_slots else START_SLOT
    max_sloads_per_tx = _max_sloads_per_tx(tx_gas_limit, fork)

    # Pre-load slot 0 with the starting offset. For existing_slots,
    # also fill the slot range the loop will read so SLOADs land on
    # populated entries rather than empty slots. A fresh Storage
    # instance is built per deployment (below) so that every target
    # gets an independent root dict, not an alias of the same one.
    storage_data: Storage.StorageDictType = {0: base_offset}
    if existing_slots:
        for i in range(base_offset, base_offset + max_sloads_per_tx):
            storage_data[i] = i

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    # Minimum per-tx gas ensuring the SLOAD loop runs at least one
    # iteration so every target satisfies storage_reads=[base_offset]:
    # intrinsic + CALL + offset_holder + setup + loop threshold
    # + one iteration + final SSTORE, with buffer.
    min_tx_gas = intrinsic_gas + 130_000

    # senders_iter yields one sender per tx (fresh per call in
    # distinct mode, a single shared sender otherwise). The senders
    # list collects one entry per tx so the BAL builder below can
    # group nonce changes by sender uniformly.
    senders_iter = _sender_generator(pre, distinct_senders)
    senders: list[EOA] = []

    gas_available = gas_benchmark_value
    targets: list[Address] = []
    txs: list[Transaction] = []

    # Each tx targets a freshly-deployed contract with identical code
    # and storage layout.
    while gas_available >= min_tx_gas:
        tx_gas = min(gas_available, tx_gas_limit)
        target = pre.deploy_contract(
            code=runtime_code,
            storage=Storage(storage_data),
        )
        targets.append(target)
        sender = next(senders_iter)
        senders.append(sender)
        txs.append(
            Transaction(
                gas_limit=tx_gas,
                to=target,
                sender=sender,
            )
        )
        gas_available -= tx_gas

    expectations: dict[Address, BalAccountExpectation] = {
        offset_holder: BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    validate_any_change=True,
                ),
            ],
        ),
    }
    for t in targets:
        expectations[t] = BalAccountExpectation(
            storage_reads=[base_offset],
            storage_changes=[
                BalStorageSlot(
                    slot=0,
                    validate_any_change=True,
                ),
            ],
        )
    sender_nonces: dict[Address, list[BalNonceChange]] = {}
    for i, s in enumerate(senders):
        changes = sender_nonces.setdefault(s, [])
        changes.append(
            BalNonceChange(
                block_access_index=i + 1,
                post_nonce=len(changes) + 1,
            )
        )
    for addr, nonces in sender_nonces.items():
        expectations[addr] = BalAccountExpectation(nonce_changes=nonces)

    blocks = [
        Block(
            txs=txs,
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations=expectations,
            ),
        )
    ]

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )
