"""Shared constants and helpers for stateful benchmark tests."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import partial

from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    Transaction,
)
from execution_testing.base_types.base_types import Number

# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)
MINT_SELECTOR = 0x40C10F19  # mint(address,uint256)


# Standard While-loop decrement-and-test condition.
#
# Expects the iteration counter on top of the stack:
#   [counter] → SUB(counter, 1) → continue if nonzero
DECREMENT_COUNTER_CONDITION = (
    Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO
)


class CacheStrategy(str, Enum):
    """Defines cache assumptions for benchmarked state access."""

    # No caching strategy: target state is cold in EVM and cache
    NO_CACHE = "no_cache"
    # Caching at tx level: target state is warm in EVM and cache
    CACHE_TX = "cache_tx"
    # Caching at previous block:
    # Target state is cold in EVM but (assumed) to be cached
    CACHE_PREVIOUS_BLOCK = "cache_previous_block"


def build_benchmark_txs(
    *,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    attack_contract_address: Address,
    setup_cost: int,
    iteration_cost: int,
    calldata_builder: Callable[[int, int], bytes] | None = None,
    access_list: list[AccessList] | None = None,
) -> tuple[list[Transaction], int]:
    """
    Build benchmark transactions filling gas_benchmark_value.

    Partition the total gas budget into transactions, each
    containing as many loop iterations as the per-tx gas limit
    allows.  Return (txs, total_gas_consumed).

    The default calldata layout is ``Hash(num_iters) +
    Hash(counter_offset)``.  Pass *calldata_builder* to override.
    """
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_intrinsic = intrinsic_cost_calc(
        access_list=access_list or [],
        calldata=b"\xff" * 64,
    )

    gas_remaining = gas_benchmark_value
    txs: list[Transaction] = []
    counter_offset = 0
    total_gas_consumed = 0

    while gas_remaining > (max_intrinsic + setup_cost + iteration_cost):
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < max_intrinsic + setup_cost:
            break

        num_iters = (
            gas_available - max_intrinsic - setup_cost
        ) // iteration_cost

        if num_iters == 0:
            break

        if calldata_builder is not None:
            calldata = calldata_builder(num_iters, counter_offset)
        else:
            calldata = bytes(Hash(num_iters) + Hash(counter_offset))
        actual_intrinsic = intrinsic_cost_calc(
            access_list=access_list or [],
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        tx_gas = actual_intrinsic + setup_cost + num_iters * iteration_cost

        txs.append(
            Transaction(
                gas_limit=tx_gas,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list or [],
            )
        )

        total_gas_consumed += tx_gas
        gas_remaining -= gas_available
        counter_offset += num_iters

    assert txs, "Gas loop produced zero transactions"
    return txs, total_gas_consumed


def build_cache_strategy_blocks(
    cache_strategy: CacheStrategy,
    txs: list[Transaction],
    cache_txs: list[Transaction],
) -> list[Block]:
    """
    Assemble benchmark blocks based on cache strategy.

    For CACHE_PREVIOUS_BLOCK, prepend a warmup block before the
    execution block so that client caches are hot but EVM state is
    cold.  Otherwise return a single execution block.
    """
    if cache_strategy != CacheStrategy.CACHE_PREVIOUS_BLOCK:
        return [Block(txs=txs)]
    return [Block(txs=cache_txs), Block(txs=txs)]


def pack_transactions_into_blocks(
    transactions: list[Transaction],
    gas_limit: int,
) -> list[Block]:
    """
    Pack transactions into blocks without exceeding gas_limit per block.

    Greedily add transactions to the current block until adding another
    would exceed the gas limit, then start a new block.
    """
    if not transactions:
        return []

    blocks: list[Block] = []
    current_txs: list[Transaction] = []
    current_gas = 0

    for tx in transactions:
        if current_gas + tx.gas_limit > gas_limit and current_txs:
            blocks.append(Block(txs=current_txs))
            current_txs = []
            current_gas = 0

        current_txs.append(tx)
        current_gas += tx.gas_limit

    if current_txs:
        blocks.append(Block(txs=current_txs))

    return blocks


def build_delegated_storage_setup(
    *,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    needs_init: bool,
    num_target_slots: int,
    initializer_code: IteratingBytecode,
    initializer_addr: Address,
    executor_addr: Address,
    authority: EOA,
    authority_nonce: int,
    delegation_sender: EOA,
    initializer_calldata_generator: Callable[[int, int], bytes],
) -> list[Block]:
    """
    Build setup blocks for delegated storage benchmarks.

    Use EIP-7702 authorization to delegate an authority EOA first to
    a storage-initializer contract (if *needs_init*), then to the
    benchmark executor contract.  Return the list of setup blocks.
    """
    blocks: list[Block] = []

    if needs_init:
        # Block 1: Authorize to initializer
        blocks.append(
            Block(
                txs=[
                    Transaction(
                        to=delegation_sender,
                        gas_limit=tx_gas_limit,
                        sender=delegation_sender,
                        authorization_list=[
                            AuthorizationTuple(
                                address=initializer_addr,
                                nonce=authority_nonce,
                                signer=authority,
                            ),
                        ],
                    )
                ]
            )
        )
        authority_nonce += 1

        # Calculate max slots per transaction based on gas cost
        iteration_cost = initializer_code.tx_gas_limit_by_iteration_count(
            fork=fork,
            iteration_count=1,
            start_iteration=1,
            calldata=initializer_calldata_generator,
        )
        iteration_count = max(1, tx_gas_limit // iteration_cost)

        init_txs: list[Transaction] = []
        for start in range(1, num_target_slots + 1, iteration_count):
            chunk_size = min(iteration_count, num_target_slots - start + 1)
            init_txs.extend(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=chunk_size,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=start,
                    calldata=initializer_calldata_generator,
                )
            )

        # Pack init transactions into blocks
        blocks.extend(pack_transactions_into_blocks(init_txs, tx_gas_limit))

    # Final block: Authorize to executor
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=delegation_sender,
                    gas_limit=tx_gas_limit,
                    sender=delegation_sender,
                    authorization_list=[
                        AuthorizationTuple(
                            address=executor_addr,
                            nonce=authority_nonce,
                            signer=authority,
                        ),
                    ],
                )
            ]
        )
    )

    return blocks


def create_sstore_initializer(init_val: int) -> IteratingBytecode:
    """
    Create a contract that initializes storage slots from calldata.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] slot count (num)

    storage[i] = init_val for i in [index, index + num).
    """
    # Setup: [index, index + num]
    prefix = (
        Op.CALLDATALOAD(0)  # [index]
        + Op.DUP1  # [index, index]
        + Op.CALLDATALOAD(32)  # [index, index, num]
        + Op.ADD  # [index, index + num]
    )

    # Loop: decrement counter and store at current position
    # Stack after subtraction: [index, current]
    # where current goes from index+num-1 down to index
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [index, current, 1]
        + Op.SWAP1  # [index, 1, current]
        + Op.SUB  # [index, current - 1]
        + Op.SSTORE(  # STORAGE[current-1] = initial_value
            Op.DUP2,
            init_val,
            key_warm=False,
            # gas accounting
            original_value=0,
            current_value=0,
            new_value=init_val,
        )
        # After SSTORE: [index, current - 1]
        # Continue while current - 1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


def initializer_calldata_generator(
    iteration_count: int, start_iteration: int
) -> bytes:
    """Generate calldata for the storage initializer."""
    return Hash(start_iteration) + Hash(iteration_count)


def create_sequential_sstore_initializer() -> IteratingBytecode:
    """
    Create a contract that initializes storage with slot-dependent values.

    - CALLDATA[0..32]  start slot (index)
    - CALLDATA[32..64] slot count (num)
    - CALLDATA[64..96] value offset

    storage[i] = i + offset for i in [index, index + num).
    """
    # Setup: [offset, index, index + num]
    prefix = (
        Op.CALLDATALOAD(64)  # [offset]
        + Op.CALLDATALOAD(0)  # [index, offset]
        + Op.DUP1  # [index, index, offset]
        + Op.CALLDATALOAD(32)  # [num, index, index, offset]
        + Op.ADD  # [num + index, index, offset]
    )

    # Loop: decrement current and store slot-dependent value
    # Stack: [current, index, offset]
    # current goes from index+num down; stores at current-1
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [1, current, index, offset]
        + Op.SWAP1  # [current, 1, index, offset]
        + Op.SUB  # [current-1, index, offset]
        + Op.DUP1  # [current-1, current-1, index, offset]
        + Op.DUP1  # [current-1, current-1, current-1, index, offset]
        + Op.DUP5  # [offset, current-1, current-1, current-1, index, offset]
        + Op.ADD  # [current-1 + offset, current-1, current-1, index, offset]
        + Op.SWAP1  # [current-1, current-1 + offset, current-1, index, offset]
        + Op.SSTORE(  # SSTORE(current-1, current-1 + offset)
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        # Stack: [current-1, index, offset]
        # Continue while current-1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


def sequential_initializer_calldata_generator(
    iteration_count: int,
    start_iteration: int,
    *,
    offset: int = 0,
) -> bytes:
    """Generate calldata for the sequential storage initializer."""
    return Hash(start_iteration) + Hash(iteration_count) + Hash(offset)


@dataclass(frozen=True)
class StorageInitRange:
    """One contiguous range of storage to initialize."""

    start_slot: int
    num_slots: int
    offset: int


def build_sequential_storage_init(
    *,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    authority: EOA,
    storage_init_ranges: list[StorageInitRange],
) -> list[Block]:
    """
    Build blocks that initialize storage with slot-dependent values.

    Deploy a sequential-SSTORE initializer, delegate *authority* to it,
    and emit transactions that write
    ``storage[i] = i + range.offset`` for every range.  The authority's
    nonce is incremented in-place.
    """
    initializer_code = create_sequential_sstore_initializer()
    initializer_addr = pre.deploy_contract(code=initializer_code)

    delegation_sender = pre.fund_eoa()
    auth_tx = Transaction(
        to=delegation_sender,
        gas_limit=tx_gas_limit,
        sender=delegation_sender,
        authorization_list=[
            AuthorizationTuple(
                address=initializer_addr,
                nonce=authority.nonce,
                signer=authority,
            ),
        ],
    )
    authority.nonce = Number(authority.nonce + 1)

    init_txs: list[Transaction] = []
    for r in storage_init_ranges:
        if r.num_slots == 0:
            continue
        calldata_gen = partial(
            sequential_initializer_calldata_generator,
            offset=r.offset,
        )
        iteration_cost = initializer_code.tx_gas_limit_by_iteration_count(
            fork=fork,
            iteration_count=1,
            start_iteration=max(1, r.start_slot),
            calldata=calldata_gen,
        )
        iteration_count = max(1, tx_gas_limit // iteration_cost)

        end_slot = r.start_slot + r.num_slots
        for start in range(r.start_slot, end_slot, iteration_count):
            chunk = min(iteration_count, end_slot - start)
            init_txs.extend(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=chunk,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=start,
                    calldata=calldata_gen,
                )
            )

    blocks: list[Block] = [Block(txs=[auth_tx])]
    blocks.extend(pack_transactions_into_blocks(init_txs, tx_gas_limit))
    return blocks
