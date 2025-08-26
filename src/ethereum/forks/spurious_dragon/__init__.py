"""
The Spurious Dragon fork is the second of two forks responding to a
denial-of-service attack on the Ethereum network. It tunes the prices of EVM
instructions, adds protection against replaying transaction on different
chains, limits the maximum size of contract code, and enables the removal of
empty accounts.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(2675000)
