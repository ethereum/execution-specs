"""Transaction and block packing helpers for benchmark gas budgets."""

from collections.abc import Callable, Sequence

from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Block,
    Fork,
    Hash,
    Transaction,
    TransactionWithCost,
)

from .enums import CacheStrategy


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
    txs: Sequence[Transaction],
    cache_txs: Sequence[Transaction],
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
        tx_gas_limit = tx.gas_limit
        if current_gas + tx_gas_limit > gas_limit and current_txs:
            blocks.append(Block(txs=current_txs))
            current_txs = []
            current_gas = 0

        current_txs.append(tx)
        current_gas += tx_gas_limit

    if current_txs:
        blocks.append(Block(txs=current_txs))

    return blocks


def pack_transactions_with_cost_into_blocks(
    transactions: list[TransactionWithCost],
    gas_limit: int,
) -> list[Block]:
    """
    Pack transactions into blocks, tracking both gas dimensions.

    A transaction is includable only while its gas limit still fits the
    room left in the regular and in the state dimension alike, so the
    room a block has left is measured against the larger of the two
    running totals. Raise when a single transaction cannot fit an empty
    block, which no packing can rescue.
    """
    if not transactions:
        return []

    blocks: list[Block] = []
    current_txs: list[TransactionWithCost] = []
    current_regular = 0
    current_state = 0

    for tx in transactions:
        tx_gas_limit = int(tx.gas_limit)
        if tx_gas_limit > gas_limit:
            raise ValueError(
                f"transaction gas limit {tx_gas_limit} exceeds the "
                f"{gas_limit} block gas limit"
            )
        room = gas_limit - max(current_regular, current_state)
        if tx_gas_limit > room and current_txs:
            blocks.append(Block(txs=current_txs))
            current_txs = []
            current_regular = 0
            current_state = 0

        current_txs.append(tx)
        current_regular += tx.execution_cost
        current_state += tx.state_cost

    if current_txs:
        blocks.append(Block(txs=current_txs))

    return blocks
