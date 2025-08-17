"""
State Oracle Interface for Ethereum Execution Specs.

Provides an abstract interface for state access that can be implemented
by different state management strategies.
"""

from .interface import MerkleOracle
from .memory_oracle import MemoryMerkleOracle

__all__ = [
    "MerkleOracle",
    "MemoryMerkleOracle",
]
