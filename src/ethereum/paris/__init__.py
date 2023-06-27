"""
Ethereum Paris Hardfork
^^^^^^^^^^^^^^^^^^^^^^^

The Fourteenth Ethereum hardfork.
"""

from ethereum.fork_criteria import ByBlockNumber

# The actual trigger for the Paris hardfork was The Merge occurring when
# total difficulty (the sum of the all block difficulties) reached the
# Terminal Total Difficulty value (58750000000000000000000 on Mainnet). The
# Merge is now a historical event.
FORK_CRITERIA = ByBlockNumber(15537394)
