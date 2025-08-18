"""
State Oracle Interface for Ethereum Execution Specs.

Provides an abstract interface for state access that can be implemented
by different state management strategies.
"""

from typing import Optional

from .interface import MerkleOracle
from .memory_oracle import MemoryMerkleOracle

_state_oracle: Optional[MerkleOracle] = None


def set_state_oracle(oracle: MerkleOracle) -> Optional[MerkleOracle]:
    """
    Set the global state oracle.

    Returns the previous oracle if any.
    """
    global _state_oracle
    old = _state_oracle
    _state_oracle = oracle
    return old


def get_state_oracle() -> MerkleOracle:
    """
    Get the current global state oracle.

    Raises RuntimeError if no oracle has been set.
    """
    global _state_oracle
    if _state_oracle is None:
        raise RuntimeError(
            "No global state oracle set. Call set_state_oracle() first."
        )
    return _state_oracle


__all__ = [
    "MerkleOracle",
    "MemoryMerkleOracle",
    "set_state_oracle",
    "get_state_oracle",
]
