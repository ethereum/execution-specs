"""Transaction and block packing helpers for benchmark gas budgets."""

from collections.abc import Callable, Sequence

from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Block,
    Fork,
    Hash,
    TestPhaseManager,
    Transaction,
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


# Every stateful benchmark is measured on a client process that was started
# for it, so the payload under test would otherwise be charged the one-off
# cost of reaching a steady state.  These two constants are that standard:
# the same preamble runs ahead of every benchmark, whatever the scenario.
#
# The transaction count is the cheap half.  A transaction costs microseconds
# where a block costs tens of milliseconds, so the count sits above the
# invocation thresholds at which JIT runtimes promote a method out of their
# first tier - .NET at 30, the JVM's first profiled tier at 200 - with
# headroom, because .NET does not begin counting until a startup delay has
# expired.
STARTUP_BLOCK_TX_COUNT = 256

# Block count is the expensive half, so it buys only what is measurably
# worth it: leaving the first block, where the per-block cost is several
# times its steady state, plus margin.  Reaching the same threshold per
# block would take thirty of them and is not worth the run time.
STARTUP_BLOCK_COUNT = 4


def build_startup_blocks(pre: Alloc) -> list[Block]:
    """
    Build the setup blocks that precede every stateful benchmark.

    A client pays one-off costs on the first blocks a process sees: compiling
    its hot paths, filling caches that start empty, opening database handles.
    Running the same preamble ahead of every benchmark keeps that cost out of
    the measurement and, just as important, keeps it equal across scenarios.

    Every account touched here is created by these blocks, so the state the
    benchmark reads stays cold.  The transactions are plain transfers: they
    exercise the per-transaction path, while the loop-heavy code the benchmark
    itself runs reaches optimised code from its own iteration count.
    """
    with TestPhaseManager.setup():
        sender = pre.fund_eoa()
        return [
            Block(
                txs=[
                    Transaction(
                        to=pre.fund_eoa(amount=0),
                        value=1,
                        sender=sender,
                    )
                    # Only the first block carries the transactions; the rest
                    # are there for the per-block cost and stay cheap.
                    for _ in range(STARTUP_BLOCK_TX_COUNT if i == 0 else 1)
                ]
            )
            for i in range(STARTUP_BLOCK_COUNT)
        ]


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
