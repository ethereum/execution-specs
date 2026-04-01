"""Shared constants and helpers for stateful benchmark tests."""

from collections.abc import Callable
from enum import Enum

from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    Block,
    Fork,
    Hash,
    Op,
    Transaction,
)
from execution_testing.base_types import Number
from execution_testing.rpc import EthRPC

# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)
MINT_SELECTOR = 0x40C10F19  # mint(address,uint256)

# Storage-bloated EOA private keys, keyed by bloat size identifier.
# Addresses derived via: keccak256(utf8ToBytes("stateBloaters{N}"))
_STORAGE_BLOATED_EOA_KEYS: dict[str, str] = {
    "1GB": (
        "0xc618d7bcd54de2f0dcf86e4ced86ccf07926619a74ee10432c3d1c60743e3427"
    ),
    "10GB": (
        "0x4da32d29f6dcffa26e09dc4e102033f2d105de1444fb893493ae703289275e0e"
    ),
    "20GB": (
        "0xc025d5a1aa0f5eee1f50687901c5dc9a8e97a2be91aa381e4c938dc309105059"
    ),
}

STORAGE_BLOATED_EOAS: list[str] = list(_STORAGE_BLOATED_EOA_KEYS.keys())


def get_storage_bloated_eoa(
    name: str,
    eth_rpc: EthRPC | None = None,
) -> EOA:
    """Return an EOA for a storage-bloated account with its on-chain nonce."""
    eoa = EOA(key=_STORAGE_BLOATED_EOA_KEYS[name])
    if eth_rpc is not None:
        nonce = eth_rpc.get_transaction_count(Address(eoa))
        eoa.nonce = Number(nonce)
    return eoa


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
