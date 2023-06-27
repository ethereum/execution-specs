"""
Ethereum Homestead Hardfork
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The second Ethereum hardfork.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(1150000)
