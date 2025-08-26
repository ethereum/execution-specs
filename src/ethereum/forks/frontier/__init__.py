"""
Frontier is the first production-ready iteration of the Ethereum protocol.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(0)
