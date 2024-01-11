"""
The Byzantium fork reduces the mining rewards, delays the difficulty bomb,
lets contracts make non-state-changing calls to other contracts, and adds
cryptographic primitives for layer 2 scaling.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(4370000)
