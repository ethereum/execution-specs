"""Shared constants and helpers for stateful benchmark tests."""

import json
from collections.abc import Callable
from enum import Enum
from pathlib import Path

from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Fork,
    Hash,
    Op,
    Transaction,
)

# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)
MINT_SELECTOR = 0x40C10F19  # mint(address,uint256)

# Load token names from stubs_bloatnet.json for test parametrization
_STUBS_FILE = Path(__file__).parent / "bloatnet" / "stubs_bloatnet.json"
with open(_STUBS_FILE) as f:
    _STUBS = json.load(f)

# Extract unique token names for each test type
SLOAD_TOKENS = [
    k.replace("test_sload_empty_erc20_balanceof_", "")
    for k in _STUBS.keys()
    if k.startswith("test_sload_empty_erc20_balanceof_")
]
SSTORE_TOKENS = [
    k.replace("test_sstore_erc20_approve_", "")
    for k in _STUBS.keys()
    if k.startswith("test_sstore_erc20_approve_")
]
SSTORE_MINT_TOKENS = [
    k.replace("test_sstore_erc20_mint_", "")
    for k in _STUBS.keys()
    if k.startswith("test_sstore_erc20_mint_")
]
MIXED_TOKENS = [
    k.replace("test_mixed_sload_sstore_", "")
    for k in _STUBS.keys()
    if k.startswith("test_mixed_sload_sstore_")
]

# Extract factory stub names for factory-based benchmarks,
# sorted by bytecode size
FACTORY_STUBS = sorted(
    [k for k in _STUBS if k.startswith("bloatnet_factory_")],
    key=lambda name: float(
        name.replace("bloatnet_factory_", "")
        .replace("kb", "")
        .replace("_", ".")
    ),
)
assert FACTORY_STUBS, "No factory stubs found matching 'bloatnet_factory_*'"

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
