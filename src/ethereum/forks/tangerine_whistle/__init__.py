"""
The Tangerine Whistle fork is the first of two forks responding to a
denial-of-service attack on the Ethereum network. It tunes the price of various
EVM instructions, and reduces the state size by removing a number of empty
accounts.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(2463000)
