"""
Frontier is the first production-ready iteration of the Ethereum protocol.
"""

from ethereum.fork_criteria import ByBlockNumber, ForkCriteria

FORK_CRITERIA: ForkCriteria = ByBlockNumber(0)
