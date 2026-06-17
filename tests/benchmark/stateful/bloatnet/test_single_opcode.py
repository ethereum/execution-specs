"""
abstract: BloatNet single-opcode benchmark cases for state-related operations.

   These tests focus on individual EVM opcodes (SLOAD, SSTORE) to measure
   their performance when accessing many storage slots across pre-deployed
   contracts. Unlike multi-opcode tests, these isolate single operations
   to benchmark specific state-handling bottlenecks.
"""

from functools import partial
from typing import Any, Callable, Generator, List

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
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
    Storage,
    TestPhaseManager,
    Transaction,
    While,
)
from execution_testing.base_types.base_types import Number

from tests.benchmark.stateful.helpers import (
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
    CacheStrategy,
    build_cache_strategy_blocks,
    build_delegated_storage_setup,
    create_sstore_initializer,
    initializer_calldata_generator,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"

# keccak256("random") for non-existing slots, masked as address,
# Solidity does input checks on the size and throws if we input
# something different than an address
START_SLOT = (
    0xA4896A3F93BF4BF58378E579F3CF193BB4AF1022AF7D2089F37D8BAE7157B85F
    % (2**160)
)


def _max_sloads_per_tx(tx_gas_limit: int, fork: Fork) -> int:
    """
    Conservative upper bound on cold SLOADs that fit in a max-gas tx.

    Derived from the cold SLOAD cost (EIP-2929: 2100 gas) and used by
    the bloated SLOAD benchmarks both as the inter-tx offset stride
    (to keep consecutive txs' SLOAD ranges disjoint) and as the
    per-target storage pre-load count.
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


def delegate_with_calldata(
    pre: Alloc,
    fork: Fork,
    authority: EOA,
    address: Address,
    calldata: Hash,
) -> Transaction:
    """
    Create a tx that delegates the authority and calls it with calldata.

    The delegated code determines what happens with the calldata.
    The authority nonce is incremented in-place.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(calldata),
        authorization_list_or_count=1,
    )
    gas_limit = intrinsic_gas + 500_000
    tx = Transaction(
        gas_limit=gas_limit,
        to=authority,
        value=0,
        data=calldata,
        sender=pre.fund_eoa(),
        authorization_list=[
            AuthorizationTuple(
                chain_id=0,
                address=address,
                nonce=authority.nonce,
                signer=authority,
            ),
        ],
    )
    authority.nonce = Number(authority.nonce + 1)
    return tx


def run_bloated_eoa_benchmark(
    *,
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    authority: EOA,
    existing_slots: bool,
    runtime_code: Bytecode,
    cache_strategy: CacheStrategy,
    tx_generator: Callable[[EOA], list[Transaction]] | None = None,
) -> None:
    """
    Run a bloated-EOA benchmark with the given runtime delegation code.
    """
    slot_0_value = Hash(1) if existing_slots else Hash(START_SLOT)

    setter_address = pre.deploy_contract(code=Op.SSTORE(0, Op.CALLDATALOAD(0)))
    runtime_address = pre.deploy_contract(code=runtime_code)

    init_tx = delegate_with_calldata(
        pre,
        fork,
        authority,
        setter_address,
        slot_0_value,
    )
    runtime_tx = delegate_with_calldata(
        pre,
        fork,
        authority,
        runtime_address,
        Hash(0),
    )

    blocks: list[Block] = [Block(txs=[init_tx, runtime_tx])]

    sender = pre.fund_eoa()

    txs: list[Transaction] = []
    with TestPhaseManager.execution():
        if tx_generator is not None:
            txs = tx_generator(sender)
        else:
            gas_available = gas_benchmark_value
            intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
            while gas_available >= intrinsic_gas:
                tx_gas = min(gas_available, tx_gas_limit)
                txs.append(
                    Transaction(
                        gas_limit=tx_gas,
                        to=authority,
                        sender=sender,
                    )
                )
                gas_available -= tx_gas

    cache_txs: list[Transaction] = []
    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        with TestPhaseManager.setup():
            cache_sender = pre.fund_eoa()
            for tx in txs:
                cache_txs.append(
                    Transaction(
                        gas_limit=tx.gas_limit,
                        data=tx.data,
                        to=authority,
                        sender=cache_sender,
                    )
                )

    blocks += build_cache_strategy_blocks(cache_strategy, txs, cache_txs)

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
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
            condition=Op.GT(Op.GAS, 0xFFFF),
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
    # Runtime: read old offset from slot 0, write new offset from
    # calldata to slot 0, then SLOAD sequentially from old offset.
    runtime_code = (
        Op.SLOAD(Op.PUSH0)
        + Op.SSTORE(Op.PUSH0, Op.CALLDATALOAD(Op.PUSH0))
        + While(
            body=(Op.DUP1 + Op.SLOAD + Op.POP + Op.PUSH1(1) + Op.ADD),
            condition=Op.GT(Op.GAS, 0xFFFF),
        )
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
    )

    # senders_iter yields one sender per tx (fresh per call in
    # distinct mode, a single shared sender otherwise). The senders
    # list collects one entry per tx so the BAL builder below can
    # group nonce changes by sender uniformly.
    senders_iter = _sender_generator(pre, distinct_senders)
    senders: list[EOA] = []

    gas_available = gas_benchmark_value
    txs: list[Transaction] = []

    # First transaction: minimal gas, only writes the initial
    # offset. Gas limit ensures remaining gas after the SLOAD +
    # SSTORE setup falls below the 0xFFFF loop threshold so the
    # SLOAD loop does not run. This tx's job is to change slot 0
    # inside the benchmark block so every subsequent max-gas tx
    # reads an offset the prefetcher's pre-block snapshot does
    # not see, achieving a 100% prefetch miss rate on max-gas txs.
    first_tx_gas = min(gas_available, intrinsic_gas + 30_000)
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
    while gas_available >= intrinsic_gas:
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
            condition=Op.GT(Op.GAS, 0xFFFF),
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
    # intrinsic + CALL + offset_holder + setup + 0xFFFF loop threshold
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


@pytest.mark.repricing
@pytest.mark.stub_parametrize("token_name", "bloated_eoa_")
@pytest.mark.parametrize("write_new_value", [False, True])
@pytest.mark.parametrize("existing_slots", [True, False])
@pytest.mark.parametrize("cache_strategy", [CacheStrategy.NO_CACHE])
def test_sstore_bloated(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    write_new_value: bool,
    existing_slots: bool,
    cache_strategy: CacheStrategy,
) -> None:
    """
    Benchmark SSTORE opcodes targeting an EOA with storage bloated.
    """
    sstore_metadata: dict[str, Any] = {}
    # If CACHE_TX, there would be one cold SLOAD before SSTORE
    sstore_metadata["key_warm"] = cache_strategy == CacheStrategy.CACHE_TX

    # SSTORE metadata matrix:
    #
    # existing_slots | write_new_value | original | current | new
    # ---------------+-----------------+----------+---------+-----
    # True           | True            | 1        | 1       | 2
    # True           | False           | 1        | 1       | 1
    # False          | True            | 0        | 0       | 1
    # False          | False           | 0        | 0       | 0

    initial_value = int(existing_slots)

    # When existing_slots is False, the initial value is always 0
    # Otherwise, the initial value starts at 1 instead.
    sstore_metadata["original_value"] = initial_value
    sstore_metadata["current_value"] = initial_value

    # If not writing a new value, the new value is the same as the current one
    # If writing a new value, the new value is current value + 1
    sstore_metadata["new_value"] = (
        initial_value if not write_new_value else initial_value + 1
    )

    setup = (
        Op.CALLDATALOAD(32)  # [end_slot]
        + Op.CALLDATALOAD(0)  # [counter, end_slot]
    )

    # stack element: [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST  # jump target

    # If CACHE_TX, warm the slot with a cold SLOAD before the SSTORE loop
    if cache_strategy == CacheStrategy.CACHE_TX:
        loop += Op.POP(Op.SLOAD(Op.DUP1, key_warm=False))

    sstore_op: Bytecode = Bytecode()
    if write_new_value:
        # s[counter] = counter + 1
        sstore_op = (
            Op.DUP1  # [counter, counter, end_slot]
            + Op.DUP1  # [counter, counter, counter, end_slot]
            + Op.PUSH1(1)  # [1, counter, counter, counter, end_slot]
            + Op.ADD  # [counter+1, counter, counter, end_slot]
            + Op.SWAP1  # [counter, counter+1, counter, end_slot]
            + Op.SSTORE(**sstore_metadata)  # [counter, end_slot]
        )
    else:
        # s[counter] = counter (existing slot) or 0 (non existing slot)
        push_value = Op.DUP1 if existing_slots else Op.PUSH1(0)
        sstore_op = (
            push_value  # [value, counter, end_slot]
            + Op.DUP2  # [counter, value, counter, end_slot]
            + Op.SSTORE(**sstore_metadata)  # [counter, end_slot]
        )

    loop += sstore_op

    # stack element: [counter, end_slot]

    loop += (
        Op.PUSH1(1)  # [1, counter, end_slot]
        + Op.ADD  # [counter+1, end_slot]
        + Op.DUP2  # [end_slot, counter+1, end_slot]
        + Op.DUP2  # [counter+1, end_slot, counter+1, end_slot]
        + Op.LT  # [counter+1<end_slot, counter+1, end_slot]
        + Op.PUSH1(len(setup))  # [dest, condition, counter+1, end_slot]
        + Op.JUMPI  # [counter+1, end_slot]
    )

    runtime_code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        cleanup=Op.STOP,
        iterating_state_gas=loop.state_cost(fork),
    )

    authority = pre.stub_eoa(token_name)
    start_slot = 1 if existing_slots else START_SLOT

    def calldata_gen(iteration_count: int, start_iteration: int) -> bytes:
        return Hash(start_iteration) + Hash(start_iteration + iteration_count)

    def tx_generator(sender: EOA) -> list[Transaction]:
        return list(
            runtime_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=sender,
                to=authority,
                start_iteration=start_slot,
                calldata=calldata_gen,
            )
        )

    run_bloated_eoa_benchmark(
        benchmark_test=benchmark_test,
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        authority=authority,
        existing_slots=existing_slots,
        runtime_code=runtime_code,
        cache_strategy=cache_strategy,
        tx_generator=tx_generator,
    )


@pytest.mark.stub_parametrize(
    "erc20_stub", "test_sload_empty_erc20_balanceof_"
)
def test_sload_erc20_generic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    erc20_stub: str,
) -> None:
    """Benchmark SLOAD using ERC20 balanceOf on bloatnet."""
    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=erc20_stub,
    )
    threshold = 100000

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = Op.MSTORE(
        0,
        BALANCEOF_SELECTOR,
        # gas accounting
        old_memory_size=0,
        new_memory_size=32,
    ) + Op.MSTORE(
        32,
        Op.SLOAD(0),  # Address Offset
        # gas accounting
        old_memory_size=32,
        new_memory_size=64,
    )

    call_balance_of = Op.POP(
        Op.CALL(
            address=erc20_address,
            args_offset=32 - 4,
            args_size=32 + 4,
        )
    )

    loop = While(
        body=call_balance_of + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.GT(Op.GAS, threshold),
    )

    teardown = Op.SSTORE(0, Op.MLOAD(32))

    # Contract Deployment
    code = setup + loop + teardown
    attack_contract_address = pre.deploy_contract(code=code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Transaction Loops
    txs = []
    gas_remaining = gas_benchmark_value

    sender = pre.fund_eoa()

    while gas_remaining > intrinsic_gas:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas:
            break

        with TestPhaseManager.execution():
            txs.append(
                Transaction(
                    gas_limit=gas_available,
                    to=attack_contract_address,
                    sender=sender,
                )
            )

        gas_remaining -= gas_available

    blocks = [Block(txs=txs)]
    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )


# SLOAD BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for balances
#           │
#           │  balanceOf(address) → SLOAD(keccak256(address || slot))
#           │
#   [Attack Contract] ──CALL──► ERC20.balanceOf(random_address)
#           │
#           └─► Loop(i=0 to N):
#                 1. Generate random address from counter
#                 2. CALL balanceOf(random_address) → forces cold SLOAD
#                 3. Most addresses have zero balance → empty storage slots
#
# WHY IT STRESSES CLIENTS:
#   - Each balanceOf() call forces a cold SLOAD on a likely-empty slot
#   - Storage slot = keccak256(address || balances_slot)
#   - Random addresses ensure maximum cache misses
#   - Tests client's sparse storage handling efficiency


# SSTORE BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for allowances
#           │
#           │  approve(spender, amount)
#           │    → SSTORE(keccak256(spender || slot), amount)
#           │
#   [Attack Contract]
#       ──CALL──► ERC20.approve(counter_as_spender, counter_as_amount)
#           │
#           └─► Loop(i=0 to N):
#                 1. Use counter as both spender address and amount
#                 2. CALL approve(counter, counter) → forces cold SSTORE
#                 3. Writes to new allowance slots in sparse storage
#
# WHY IT STRESSES CLIENTS:
#   - Each approve() call forces an SSTORE to a new storage slot
#   - Storage slot = keccak256(
#       msg.sender || keccak256(spender || allowances_slot)
#     )
#   - Sequential counter ensures unique storage locations
#   - Tests client's ability to handle many storage writes
#   - Simulates real-world contract state accumulation over time


@pytest.mark.stub_parametrize("erc20_stub", "test_sstore_erc20_approve_")
def test_sstore_erc20_generic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    erc20_stub: str,
) -> None:
    """Benchmark SSTORE using ERC20 approve."""
    sender = pre.fund_eoa()

    threshold = 100_000

    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=erc20_stub,
    )

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = Op.MSTORE(
        0,
        APPROVE_SELECTOR,
    ) + Op.MSTORE(
        32,
        Op.SLOAD(0),  # Address Offset
    )

    call_approve = Op.MSTORE(
        64,
        Op.ADD(1, Op.MLOAD(32)),
    ) + Op.POP(
        Op.CALL(
            address=erc20_address,
            args_offset=28,
            args_size=68,
        )
    )

    loop = While(
        body=call_approve + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.GT(Op.GAS, threshold),
    )

    teardown = Op.SSTORE(0, Op.MLOAD(32))

    # Contract Deployment
    code = setup + loop + teardown
    attack_contract_address = pre.deploy_contract(code=code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    # Transaction Loops
    gas_remaining = gas_benchmark_value

    # Collect tx params first, then build Transaction objects
    # so that nonces are allocated contiguously per block.
    tx_gas: list[int] = []
    while gas_remaining > intrinsic_gas:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas:
            break

        tx_gas.append(gas_available)

        gas_remaining -= gas_available

    txs = []
    with TestPhaseManager.execution():
        for gas_available in tx_gas:
            txs.append(
                Transaction(
                    gas_limit=gas_available,
                    to=attack_contract_address,
                    sender=sender,
                )
            )

    blocks = [Block(txs=txs)]

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=True,
    )


def create_sstore_executor(
    sloads_before_sstore: bool,
    key_warm: bool,
    original_value: int,
    new_value: int,
) -> IteratingBytecode:
    """
    Create a contract that executes SSTORE benchmark operations.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)
    - CALLDATA[64..96] value to write

    Returns: IteratingBytecode representing the benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(64)  # value
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # [counter, value, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST
    # Loop Body: Store Value at Start Slot + Counter
    if sloads_before_sstore:
        loop += Op.DUP1  # [counter, counter, value, end_slot]
        loop += Op.SLOAD(
            # gas accounting
            key_warm=key_warm
        )
        loop += Op.POP
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter] = value
            key_warm=True,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )
    else:
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter] = value
            key_warm=key_warm,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )
    # [counter, value, end_slot]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, value, end_slot]

    # Loop Condition: Counter < end_slot
    loop += Op.DUP3  # [end_slot, counter + 1, value, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, value, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, value, end_slot]
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, value, end_slot]

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


def create_sstore_dirty_executor(
    write_values: List[int],
    key_warm: bool,
    initial_value: int,
) -> IteratingBytecode:
    """
    Create executor that writes multiple values to each slot.

    Exercise dirty state transitions by performing a sequence of SSTOREs
    to the same slot within a single loop iteration. After the first
    SSTORE, the slot is warm and subsequent writes hit the dirty
    (100 gas) path when original != current.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)

    Return an IteratingBytecode for the dirty-write benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # Stack: [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST

    for i, val in enumerate(write_values):
        is_first = i == 0
        current_val = initial_value if is_first else write_values[i - 1]
        # DUP2 reaches counter through the pushed value
        loop += Op.SSTORE(
            Op.DUP2,
            val,
            key_warm=key_warm if is_first else True,
            original_value=initial_value,
            current_value=current_val,
            new_value=val,
        )
    # Stack after all writes: [counter, end_slot]

    # Increment counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, end_slot]

    # Loop while counter + 1 < end_slot
    loop += Op.DUP2
    loop += Op.DUP2
    loop += Op.LT
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


def access_list_generator(
    iteration_count: int,
    start_iteration: int,
    access_warm: bool,
    authority: Address,
) -> list[AccessList] | None:
    """Access list generator for warming storage slots."""
    if access_warm:
        storage_keys = [
            Hash(i)
            for i in range(start_iteration, start_iteration + iteration_count)
        ]
        return [AccessList(address=authority, storage_keys=storage_keys)]
    return None


def executor_calldata_generator(
    iteration_count: int,
    start_iteration: int,
    write_value: int | None = None,
) -> bytes:
    """
    Calldata generator for executor operations.

    Generates: Hash(start) + Hash(start + count) [+ Hash(write_value)]
    """
    result = Hash(start_iteration) + Hash(start_iteration + iteration_count)
    if write_value is not None:
        result += Hash(write_value)
    return result


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize("sloads_before_sstore", [True, False])
@pytest.mark.parametrize(
    "initial_value,write_value",
    [
        pytest.param(0, 0, id="zero_to_zero"),
        pytest.param(0, 0xDEADBEEF, id="zero_to_nonzero"),
        # TODO: Resolve refund mechanism
        # pytest.param(0xDEADBEEF, 0, id="nonzero_to_zero"),
        pytest.param(0xDEADBEEF, 0xBEEFBEEF, id="nonzero_to_diff"),
        pytest.param(0xDEADBEEF, 0xDEADBEEF, id="nonzero_to_same"),
    ],
)
def test_sstore_variants(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    sloads_before_sstore: bool,
    initial_value: int,
    write_value: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations.

    Uses EIP-7702 delegation. The authority EOA delegates to:
    - StorageInitializer: storage[i] = initial_value (initial_value != 0)
    - BenchmarkExecutor: performs the benchmark operation (SSTORE)

    Variants:
    - access_warm: Warm storage slots via access list
    - sloads_before_sstore: SLOADs per slot before SSTORE
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(initial_value)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Actual Benchmark Execution
    executor_code = create_sstore_executor(
        sloads_before_sstore=sloads_before_sstore,
        key_warm=access_warm,
        original_value=initial_value,
        new_value=write_value,
    )
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(
        executor_calldata_generator, write_value=write_value
    )
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
        )
    )

    # Setup phase: initialize storage slots (if initial_value != 0)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            needs_init=initial_value != 0,
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
            )
        )

        expected_gas_used = sum(tx.gas_cost for tx in exec_txs)

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


# SSTORE DIRTY TRANSITIONS BENCHMARK ARCHITECTURE:
#
#   [Authority EOA]
#       │
#       │ Phase 1: Delegate to StorageInitializer
#       │   ──► SSTORE(slot, initial_value) for N slots
#       │
#       │ Phase 2: Delegate to DirtyExecutor
#       │   ──► For each slot:
#       │         SSTORE(slot, v1) → SSTORE(slot, v2) → ...
#       │
# WHY IT STRESSES CLIENTS:
#   - Multiple writes per slot exercise EIP-2200/EIP-3529 refund
#     branching: clean (original==current) vs dirty (original!=current)
#   - Oscillation causes refund counter to swing up/down each write
#   - Refund cap (gas_used/5) saturates with enough iterations
#   - Tests correct tracking of original vs current vs new values


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize(
    "initial_value,write_values",
    [
        pytest.param(
            0xDEADBEEF,
            [0, 0xDEADBEEF, 0, 0xDEADBEEF],
            id="oscillation_4x",
        ),
        pytest.param(
            0xDEADBEEF,
            [0, 0xDEADBEEF, 0, 0xDEADBEEF, 0, 0xDEADBEEF],
            id="oscillation_6x",
        ),
        pytest.param(
            0xDEADBEEF,
            [0xBEEFBEEF, 0xCAFECAFE, 0xDEADBEEF],
            id="triple_write_restore",
        ),
        pytest.param(
            0xDEADBEEF,
            [0],
            id="mass_clear",
        ),
        pytest.param(
            0,
            [1, 0, 1, 0],
            id="oscillation_4x_from_zero",
        ),
        pytest.param(
            0,
            [1],
            id="mass_set_from_zero",
        ),
    ],
)
def test_sstore_dirty_transitions(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    initial_value: int,
    write_values: List[int],
) -> None:
    """
    Benchmark SSTORE dirty state transitions.

    Exercise EIP-2200/EIP-3529 refund logic by writing the same slot
    multiple times per iteration. Uses EIP-7702 delegation: authority
    EOA delegates to initializer then to dirty-write executor.

    Variants:
    - oscillation: X→0→X→0, alternates clean (2900) and dirty (100)
    - triple_write_restore: X→B→C→X, all SSTORE branches
    - mass_clear: X→0, maximum per-slot refund generation
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(initial_value)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Benchmark Executor — multi-write per slot
    executor_code = create_sstore_dirty_executor(
        write_values=write_values,
        key_warm=access_warm,
        initial_value=initial_value,
    )
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(executor_calldata_generator)
    access_list_gen = partial(
        access_list_generator,
        access_warm=access_warm,
        authority=authority,
    )

    # Number of slots processable in execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata_gen,
            access_list=access_list_gen,
            start_iteration=1,
        )
    )

    # Setup phase: initialize all slots to initial_value
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            needs_init=initial_value != 0,
            num_target_slots=num_target_slots,
            initializer_code=initializer_code,
            initializer_addr=initializer_addr,
            executor_addr=executor_addr,
            authority=authority,
            authority_nonce=authority_nonce,
            delegation_sender=delegation_sender,
            initializer_calldata_generator=(initializer_calldata_generator),
        )

    # Execution phase — no expected_benchmark_gas_used because
    # refund cap (gas_used/5) makes actual consumption non-trivial
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
            )
        )

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
    )


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
def test_storage_sload_benchmark(
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
        )
    )

    # Setup phase: initialize storage slots (if storage_keys_pre_set)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
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
def test_storage_sload_same_key_benchmark(
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
