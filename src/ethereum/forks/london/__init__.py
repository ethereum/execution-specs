"""
The London fork overhauls the transaction fee market, changes gas refunds,
reserves a contract prefix for future use, and delays the difficulty bomb.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(12965000)
