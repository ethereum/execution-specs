"""
The Gray Glacier fork delays the difficulty bomb. There are no other changes
in this fork.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(15050000)
