"""Parametrization enums shared across benchmark scenarios."""

from enum import Enum, auto

from execution_testing import TxOutcome


class StorageAction(Enum):
    """Enum for storage actions."""

    READ = auto()
    WRITE_SAME_VALUE = auto()
    WRITE_NEW_VALUE = auto()


TransactionResult = TxOutcome
"""Alias for the framework outcome enum used to bill transaction gas."""


class ReturnDataStyle(Enum):
    """Helper enum to specify how return data is returned to the caller."""

    RETURN = auto()
    REVERT = auto()
    IDENTITY = auto()


class CacheStrategy(str, Enum):
    """Defines cache assumptions for benchmarked state access."""

    # No caching strategy: target state is cold in EVM and cache
    NO_CACHE = "no_cache"
    # Caching at tx level: target state is warm in EVM and cache
    CACHE_TX = "cache_tx"
    # Caching at previous block:
    # Target state is cold in EVM but (assumed) to be cached
    CACHE_PREVIOUS_BLOCK = "cache_previous_block"
