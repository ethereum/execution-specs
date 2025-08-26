"""
The Paris fork transitions Ethereum from a proof-of-work consensus model to a
proof-of-stake one. This fork is often referred to as "The Merge" because it
marks the integration of the [consensus layer] with the execution layer
(defined in this project.)

[consensus layer]: https://github.com/ethereum/consensus-specs
"""

from ethereum.fork_criteria import ByBlockNumber

# The actual trigger for the Paris hardfork was The Merge occurring when
# total difficulty (the sum of the all block difficulties) reached the
# Terminal Total Difficulty value (58750000000000000000000 on Mainnet). The
# Merge is now a historical event.
FORK_CRITERIA = ByBlockNumber(15537394)
