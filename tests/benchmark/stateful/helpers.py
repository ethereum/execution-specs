"""Shared constants and helpers for stateful benchmark tests."""

import json
from enum import Enum
from pathlib import Path

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


class CacheStrategy(str, Enum):
    """Defines cache assumptions for benchmarked state access."""

    # No caching strategy: target state is cold in EVM and cache
    NO_CACHE = "no_cache"
    # Caching at tx level: target state is warm in EVM and cache
    CACHE_TX = "cache_tx"
    # Caching at previous block:
    # Target state is cold in EVM but (assumed) to be cached
    CACHE_PREVIOUS_BLOCK = "cache_previous_block"
